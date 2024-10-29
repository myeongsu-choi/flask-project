from flask import Flask, request, jsonify, render_template, make_response
from flask_restx import Api, Resource, fields
from models import db, create_database, User, Subject, Grade
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from datetime import timedelta
import secrets, os

app = Flask(__name__)

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost/academic_records'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT 비밀 키 설정
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

# SQLAlchemy와 JWT 초기화
db.init_app(app)
jwt = JWTManager(app)

# 보안 스키마 정의 (JWT)
authorizations = {
    'Bearer Auth': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
    }
}

# API 객체 생성
api = Api(
    app, 
    version='1.0', 
    title='Academic Records API',
    description='API for managing academic records',
    authorizations=authorizations,
    security='Bearer Auth'  
)

# 사용자 인증, 사용자, 과목, 성적 관련 작업 네임스페이스 생성
ns_auth = api.namespace('auth', description='사용자 인증 관련 작업')
ns_users = api.namespace('users', description='사용자 관련 작업')
ns_subjects = api.namespace('subjects', description='과목 관련 작업')
ns_grades = api.namespace('grades', description='성적 관련 작업')

#-------------------------------------------------------------------
# 사용자 인증 관련
# ------------------------------------------------------------------

# 사용자 모델 정의
user_model = api.model('User', {
    'id': fields.String(required=True, description='학번(직번)'),
    'role': fields.String(required=True, description='역할'),
    'name': fields.String(required=True, description='이름'),
    'department': fields.String(description='학과'),
    'admission_year': fields.Integer(required=True, description='입학년도(고용년도)')
})

# 로그인 시 요청 모델 정의
login_request = api.model('Login_Request', {
    'id': fields.String(required=True, description='학번(직번)'),
    'password': fields.String(required=True, description='비밀번호'),
    'role': fields.String(required=True, description='역할')
})

# 로그인 시 응답 모델 정의
login_response = api.model('Login_Response', {
    'access_token': fields.String(required=True, description='Access token for user'),
    'refresh_token': fields.String(required=True, description='Refresh token for user'),
    'user': fields.Nested(user_model)  
})

"""----------------------------------------------------------------
    ** 사용자가 로그인 시 **
    - 입력: id, password, role
    - 반환: access_token (15분), refresh_token (30일), 사용자 정보
"""
@ns_auth.route('/login')
class UserLogin(Resource):
    @ns_auth.expect(login_request)
    @ns_auth.marshal_with(login_response, code=200)
    def post(self):
        '''사용자 로그인'''
        data = request.json
        user = User.query.filter_by(id=data['id']).first()

        if user and user.check_password(data['password']) and user.role == data['role']:
            access_token = create_access_token(identity={'id': user.id, 'role': user.role}, expires_delta=timedelta(minutes=15))
            refresh_token = create_refresh_token(identity={'id': user.id, 'role': user.role}, expires_delta=timedelta(days=30))
            return {
                'access_token' : access_token,
                'refresh_token' : refresh_token,
                'user' : {
                    'id' : user.id,
                    'role' : user.role,
                    'name' : user.name,
                    'department' : user.department,
                    'admission_year' : user.admission_year
                }
            }, 200
            
        api.abort(401, message="아이디, 비밀번호 또는 구분이 올바르지 않습니다.")


"""----------------------------------------------------------------
    ** 엑세스 토큰 만료 시 **
    - 반환: 새로운 access_token
"""
# 토근 갱신
@ns_auth.route('/refresh')
class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        '''액세스 토큰 갱신'''
        current_user = get_jwt_identity()
        access_token = create_access_token(identity=current_user)
        return jsonify(access_token=access_token)

@api.errorhandler(Exception)
def handle_error(error):
    return {'message' : str(error)}, getattr(error, 'code', 500)


#-------------------------------------------------------------------
# 사용자 정보 CRUD 관련
# ------------------------------------------------------------------
"""----------------------------------------------------------------
    ** READ
        관리자가 모든 사용자 조회 시 **
        - 반환 : 등록되어 있는 모든 사용자 정보 

    ** CREATE
        신규 사용자가 회원가입 시 **
        - 입력 : 신규 사용자의 정보
        - 반환 : 신규 사용자의 정보
"""
@ns_users.route('/')
class UserList(Resource):
    @ns_users.doc('list_users')
    @ns_users.marshal_list_with(user_model)
    @jwt_required()
    def get(self):
        '''모든 사용자 조회'''
        current_user = get_jwt_identity() 
        if current_user['role'] != 'admin':
            api.abort(403, message="관리자만 접근 가능합니다.")
        users = User.query.all()
        return users
    
    @ns_users.doc('create_user')
    @ns_users.expect(user_model)
    @ns_users.marshal_list_with(user_model, code=201)
    def post(self):
        '''신규 사용자 생성'''
        data = request.json
        if data['role'] != 'student' and data['role'] != 'professor':
            api.abort(400, message="사용자 구분이 명확하지 않습니다.")
        user = User (
            id=data['id'],
            role=data['role'],
            name=data['name'],
            department=data['department'],
            admission_year=data['admission_year']
        )
        user.set_password('1234') 
        db.session.add(user)
        db.session.commit()
        return user, 201

"""----------------------------------------------------------------
    ** READ
        학생이나 교수가 자신의 정보를 불러오거나 관리자가 특정 학생의 정보를 불러올 시 **
        - 입력 : 해당 사용자의 ID
        - 반환 : 해당 사용자의 정보

    ** DELETE
        관리자가 특정 학생을 사용자 정보 리스트에서 삭제할 시 **
        - 입력 : 삭제할 사용자의 ID

    ** UPDATE
        관리자가 특정 학생의 정보를 수정할 시 **
        - 입력 : 수정할 사용자의 ID
"""
@ns_users.route('/<id>')
@ns_users.param('id', '사용자 학번(직번)')
class UserResource(Resource):
    @ns_users.doc('get_user')
    @ns_users.marshal_with(user_model)
    @jwt_required()
    def get(self, id):
        """특정 사용자 조회"""
        current_user = get_jwt_identity()
        if (current_user['role'] == 'student' and current_user['id'] != id) and current_user['role'] != 'admin':
            api.abort(403, message="해당 데이터의 접근 권한이 없습니다.")
            
        user = User.query.get(id)
        if not user:
            api.abort(404, message="정보를 찾을 수 없습니다.")
        return user

    @ns_users.doc('delete_user')
    @ns_users.response(204, 'User deleted')
    @jwt_required()
    def delete(self, id):
        """특정 사용자 삭제"""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': '해당 데이터의 삭제 권한이 없습니다.'}, 403

        user = User.query.get(id)
        if not user:
            api.abort(404, message="사용자를 찾을 수 없습니다.")
        db.session.delete(user)
        db.session.commit()
        return '데이터를 삭제했습니다.', 204
    
    @ns_users.doc('update_user')
    @ns_users.expect(user_model)
    @ns_users.marshal_with(user_model)
    @jwt_required()
    def put(self, id):
        """특정 사용자 정보 수정"""
        current_user = get_jwt_identity()
        
        if current_user['id'] != id and current_user['role'] != 'admin':
            api.abort(403, message="해당 데이터의 수정 권한이 없습니다.")
        
        user = User.query.get(id)
        if not user:
            api.abort(404, message="사용자를 찾을 수 없습니다.")
        
        data = request.json
        
        if 'name' in data:
            user.name = data['name']
        if 'department' in data:
            user.department = data['department']
        if 'admission_year' in data:
            user.admission_year = data['admission_year']
        if 'role' in data and (data['role'] == 'student' or data['role'] == 'professor'):
            user.role = data['role']
        else:
            api.abort(400, message="사용자 구분이 명확하지 않습니다.")
        
        db.session.commit()
        return user


#-------------------------------------------------------------------
# 과목 정보 CRUD
# ------------------------------------------------------------------

# 과목 모델 정의
subject_model = api.model('Subject', {
    'code': fields.String(required=True, description='과목 코드'),
    'name': fields.String(required=True, description='과목명'),
    'credits': fields.Integer(required=True, description='학점'),
    'professor_id': fields.String(description='교수 ID')
})

"""
    ** READ
        사용자가 모든 과목 조회 시 **
        - 반환 : 등록되어 있는 모든 과목 정보 

    ** CREATE
        관리자가 신규 과목 생성 시 **
        - 입력 : 신규 과목의 정보
        - 반환 : 신규 과목의 정보
"""
@ns_subjects.route('/')
class SubjectList(Resource):
    @ns_subjects.doc('list_subjects')
    @ns_subjects.marshal_list_with(subject_model)
    def get(self):
        """모든 과목 조회"""
        subjects = Subject.query.all()
        return subjects

    @ns_subjects.doc('create_subject')
    @ns_subjects.expect(subject_model)
    @ns_subjects.marshal_with(subject_model, code=201)
    @jwt_required()
    def post(self):
        """새 과목 추가"""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            api.abort(403, message="관리자만 접근 가능합니다.")

        data = request.json
        subject = Subject(
            code=data['code'],
            name=data['name'],
            credits=data['credits'],
            professor_id=data.get('professor_id')
        )
        db.session.add(subject)
        db.session.commit()
        return subject, 201

"""----------------------------------------------------------------
    ** READ
        1. 모든 사용자가 특정 과목의 정보를 불러올 시
        - 입력 : 해당 과목의 이름
        - 반환 : 해당 과목의 정보

        2. 관리자가 특정 교수, 교수가 자신이 담당하는 과목의 정보를 불러올 시 **
        - 입력 : 교수의 ID
        - 반환 : 해당 교수가 담당하는 과목

    ** DELETE
        관리자가 특정 과목을 과목 정보 리스트에서 삭제할 시 **
        - 입력 : 삭제할 과목 이름

    ** UPDATE
        관리자가 특정 과목의 정보를 수정할 시 **
        - 입력 : 수정할 과목의 이름
"""
@ns_subjects.route('/<subject_name>')
@ns_subjects.param('subject_name', '과목 이름')
class SubjectResource(Resource):
    @ns_subjects.doc('get_subject')
    @ns_subjects.marshal_with(subject_model)
    def get(self, subject_name):
        """특정 과목 조회"""

        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            api.abort(404, "과목을 찾을 수 없습니다.")
        return subject

    @ns_subjects.doc('delete_subject')
    @ns_subjects.response(204, 'Subject deleted')
    @jwt_required()
    def delete(self, subject_name):
        """특정 과목 삭제"""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            return {'message': '해당 데이터의 삭제 권한이 없습니다.'}, 403

        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            api.abort(404, message="과목을 찾을 수 없습니다.")
        db.session.delete(subject)
        db.session.commit()
        return '데이터를 삭제했습니다.', 204

    @ns_subjects.doc('update_subject')
    @ns_subjects.expect(subject_model)
    @ns_subjects.marshal_with(subject_model)
    @jwt_required()
    def put(self, subject_name):
        """특정 과목 수정"""
        current_user = get_jwt_identity()
        if current_user['role'] != 'admin':
            api.abort(403, message="해당 데이터의 수정 권한이 없습니다.")

        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            api.abort(404, message="해당 과목을 찾을 수 없습니다.")

        data = request.json
        subject.code = data.get('code', subject.code)
        subject.name = data.get('name', subject.name)
        subject.credits = data.get('credits', subject.credits)
        subject.professor_id = data.get('professor_id', subject.professor_id)
        db.session.commit()
        return subject

@ns_subjects.route('/professor/<professor_id>')
@ns_subjects.param('professor_id', '교수 직번')
class ProfessorSubjects(Resource):
    @ns_subjects.doc('get_subjects')
    @ns_subjects.marshal_list_with(subject_model)
    @jwt_required()
    def get(self, professor_id):
        """교수 담당 과목 조회"""
        current_user = get_jwt_identity()
        if (current_user['role'] == 'professor' and current_user['id'] != professor_id) or current_user['role'] == 'student':
            api.abort(403, message="데이터에 접근 권한이 없습니다.")

        subject = Subject.query.filter_by(professor_id=professor_id).all()
        if not subject:
            api.abort(404, "과목을 찾을 수 없습니다.")

        return subject

#-------------------------------------------------------------------
# 학생별 전체 성적 조회 / 과목별, 학기별 성적 조회
# ------------------------------------------------------------------

# 성적 모델 정의
grade_model = api.model('Grade', {
    'id': fields.Integer(readOnly=True, description='성적 ID'),
    'student_id': fields.String(required=True, description='학생 ID'),
    'subject_code': fields.String(required=True, description='과목 코드'),
    'subject_name': fields.String(required=True, description='과목명'),
    'semester': fields.String(required=True, description='학기'),
    'score': fields.Float(required=True, description='성적 점수'),
    'grade': fields.String(required=True, description='성적 학점')
})

"""
    ** 학생이 자신의 성적을 조회할 시,
       관리자나 교수가 특정 학생의 성적을 조회할 시 **

    - 입력 : student_id : 조회할 학생의 ID
            (과목코드를 과목명으로 바꾸기 위해 subject_code를 사용하여 Subject 테이블에서
              해당 과목의 이름(subject.name)을 조회하여 성적 정보에 포함시킴.)

    - 반환 : 해당 학생의 성적 목록
"""
@ns_grades.route('/student/<student_id>')
@ns_grades.param('student_id', '학번')
class StudentGrades(Resource):
    @ns_grades.doc('get_grades')
    @ns_grades.marshal_list_with(grade_model)
    @jwt_required()
    def get(self, student_id):
        """특정 학생의 성적 조회"""
        current_user = get_jwt_identity()
        if current_user['role'] == 'student' and current_user['id'] != student_id:
            api.abort(403, message="데이터에 접근 권한이 없습니다.")
        
        grades = Grade.query.filter_by(student_id=student_id).all()
        if not grades:
            api.abort(404, "학생의 성적을 찾을 수 없습니다.")
        
        grade_data = []
        for grade in grades:
            subject = Subject.query.filter_by(code=grade.subject_code).first()
            grade_data.append({
                'id': grade.id,
                'student_id': grade.student_id,
                'subject_code': grade.subject_code,
                'subject_name': subject.name if subject else '과목 이름 없음',  
                'semester': grade.semester,
                'score': grade.score,
                'grade': grade.grade
            })

        return grade_data

"""
    ** 학생이 자신이 수강한 특정 과목의 성적을 조회할 시,
       교수가 자신이 담담하는 과목의 성적을 조회할 시,
       관리자가 특정과목의 성적을 모두 조회할 시**
    
    - 입력 : subject_name : 조회할 과목의 이름

    - 반환 : 해당 과목의 성적
"""
@ns_grades.route('/subject/<subject_name>')
@ns_grades.param('subject_name', '과목 이름')
class SubjectGrades(Resource):
    @ns_grades.doc('get_grades_by_subject_name')
    @ns_grades.marshal_list_with(grade_model)
    @jwt_required()
    def get(self, subject_name):
        """특정 과목의 성적 조회"""
        current_user = get_jwt_identity()

        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            api.abort(404, message="해당 과목을 찾을 수 없습니다.")

        if current_user['role'] == 'student':
            grades = Grade.query.filter_by(subject_code=subject.code, student_id=current_user['id']).all()
            if not grades:
                api.abort(404, message="해당 과목의 성적이 없습니다.")

        elif current_user['role'] == 'professor':
            if subject.professor_id != current_user['id']:
                api.abort(403, message="담당하지 않은 과목의 성적은 조회할 수 없습니다.")
            grades = Grade.query.filter_by(subject_code=subject.code).all()
            if not grades:
                api.abort(404, message="해당 과목의 성적이 없습니다.")

        elif current_user['role'] == 'admin':
            grades = Grade.query.filter_by(subject_code=subject.code).all()
            if not grades:
                api.abort(404, message="해당 과목의 성적이 없습니다.")
        else:
            api.abort(403, message="접근 권한이 없습니다.")

        grade_data = []
        for grade in grades:
            grade_data.append({
                'id': grade.id,
                'student_id': grade.student_id,
                'subject_name': subject.name,
                'semester': grade.semester,
                'score': grade.score,
                'grade': grade.grade
            })

        return grade_data

"""
    ** 학생이 특정 학기에서 자신이 수강한 성적을 조회할 시,
       교수가 특정 학기에서 자신이 담당한 과목의 성적을 조회할 시,
       관리자가 특정 학기의 성적을 모두 조회할 시 **
    
    - 입력 : subject_name : 조회할 과목의 이름

    - 반환 : 해당 과목의 성적
"""
@ns_grades.route('/semester/<semester>')
@ns_grades.param('semester', '학기')
class SemesterGrades(Resource):
    @ns_grades.doc('get_grades_by_semester')
    @ns_grades.marshal_list_with(grade_model)
    @jwt_required()
    def get(self, semester):
        """특정 학기의 성적 조회"""
        current_user = get_jwt_identity()

        if current_user['role'] == 'student':
            grades = Grade.query.filter_by(student_id=current_user['id'], semester=semester).all()
            if not grades:
                api.abort(404, message=f"{semester} 학기에 해당하는 성적이 없습니다.")

        elif current_user['role'] == 'professor':
            subjects = Subject.query.filter_by(professor_id=current_user['id']).all()
            subject_codes = [subject.code for subject in subjects]
            grades = Grade.query.filter(Grade.subject_code.in_(subject_codes), Grade.semester == semester).all()
            if not grades:
                api.abort(404, message="해당 학기에 담당한 과목의 성적이 없습니다.")

        elif current_user['role'] == 'admin':
            grades = Grade.query.filter_by(semester=semester).all()
            if not grades:
                api.abort(404, message="해당 학기에 담당한 과목의 성적이 없습니다.")
        else:
            api.abort(403, message="접근 권한이 없습니다.")

        grade_data = []
        for grade in grades:
            grade_data.append({
                'id': grade.id,
                'student_id': grade.student_id,
                'subject_code': grade.subject_code,
                'subject_name' : grade.subject.name,
                'semester': grade.semester,
                'score': grade.score,
                'grade': grade.grade
            })

        return grade_data, 200

#-------------------------------------------------------------------
# 성적 입력, 수정
# ------------------------------------------------------------------
"""
    ** 교수가 담당 과목에서 성적을 추가할 시,
       관리자가 모든 과목에 성적을 추가할 시 **

       - 반환 : 추가한 성적 모델의 정보
"""
@ns_grades.route('/')
class GradeList(Resource):
    @ns_grades.doc('add_grade')
    @ns_grades.expect(grade_model)
    @ns_grades.marshal_with(grade_model, code=201)
    @jwt_required()
    def post(self):
        """성적 입력 (교수: 담당 과목만, 관리자: 모든 과목)"""
        current_user = get_jwt_identity()

        if current_user['role'] not in ['professor', 'admin']:
            api.abort(403, message="접근 권한이 없습니다.")

        data = request.json
        subject = Subject.query.filter_by(code=data['subject_code']).first()

        if not subject:
            api.abort(404, message="해당 과목을 찾을 수 없습니다.")

        if current_user['role'] == 'professor' and subject.professor_id != current_user['id']:
            api.abort(403, message="담당하지 않은 과목에 성적을 입력할 수 없습니다.")

        existing_grade = Grade.query.filter_by(
            student_id=data['student_id'],
            subject_code=data['subject_code'],
            semester=data['semester']
        ).first()
        if existing_grade:
            api.abort(400, message='해당 과목의 성적이 이미 존재합니다.')

        grade = Grade(
            student_id=data['student_id'],
            subject_code=data['subject_code'],
            semester=data['semester'],
            score=data['score'],
            grade=data['grade']
        )
        db.session.add(grade)
        db.session.commit()
        return grade, 201

"""
    ** 교수가 담당 과목의 성적을 수정할 시,
       관리자가 모든 과목의 성적을 수정할 시 **
    
        - 반환 : 수정된 성적 모델의 정보
"""

# 성적 수정 모델 정의
grade_input_model = api.model('GradeInput', {
    'score': fields.Float(required=True, description='성적 점수'),
    'grade': fields.String(required=True, description='성적 학점')
})

@ns_grades.route('/student/<string:student_id>/semester/<string:semester>/subject/<string:subject_code>')
@ns_grades.param('student_id', '학생 ID')
@ns_grades.param('semester', '학기')
@ns_grades.param('subject_code', '과목 코드')
class GradeResource(Resource):
    @ns_grades.doc('update_grade')
    @ns_grades.expect(grade_input_model)
    @ns_grades.marshal_with(grade_model)
    @jwt_required()
    def put(self, student_id, semester, subject_code):
        """성적 수정 (교수: 담당 과목만, 관리자: 모든 과목)"""
        current_user = get_jwt_identity()

        if current_user['role'] not in ['professor', 'admin']:
            api.abort(403, message="접근 권한이 없습니다.")

        grade = Grade.query.filter_by(student_id=student_id, semester=semester, subject_code=subject_code).first()
        if not grade:
            api.abort(404, message="해당 성적 정보를 찾을 수 없습니다.")

        subject = Subject.query.filter_by(code=subject_code).first()
        if current_user['role'] == 'professor' and subject.professor_id != current_user['id']:
            api.abort(403, message="담당하지 않은 과목의 성적을 수정할 수 없습니다.")

        data = request.json
        grade.score = data.get('score', grade.score)
        grade.grade = data.get('grade', grade.grade)

        db.session.commit()
        return {
            'id': grade.id,
            'student_id': grade.student_id,
            'subject_code': grade.subject_code,
            'subject_name' : grade.subject.name,
            'semester': grade.semester,
            'score': grade.score,
            'grade': grade.grade
        }, 200

# -----------------------------------------------------------------------------------#

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def student_dashboard():
    return render_template('dashboard.html')

@app.route('/grades/create')
def create_grades():
    return render_template('create_grades.html')

@app.route('/grades/manage')
def manage_grades():
    return render_template('manage_grades.html')

with app.app_context():
    create_database()
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)