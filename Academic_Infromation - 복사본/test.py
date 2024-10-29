import unittest
from flask import json
from restful_api import app  

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

# ------------------------------
#   로그인 테스트
# ------------------------------
class TestAuthAPI(BaseTestCase):
    # @ns_auth.route('/login') 관련 테스트 2개
    # ** 로그인 성공 **
    def test_login_user(self):
        login_data = {
            'id' : '2020001',
            'password' : '1234',
            'role' : 'student'
        }
        response = self.app.post('/auth/login', data=json.dumps(login_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))

        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        
        self.assertIn('user', data)
        self.assertEqual(data['user']['id'], '2020001')
        self.assertEqual(data['user']['role'], 'student')

    # ** 로그인 실패 **
    def test_login_failure(self): 
        login_data = {
            'id': '2020001', 
            'password': 'wrongpassword',  
            'role': 'student'
        }
        response = self.app.post('/auth/login', data=json.dumps(login_data),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)
        data = response.get_json()

        self.assertEqual(data['message'], '아이디, 비밀번호 또는 구분이 올바르지 않습니다.')

# ------------------------------
#   토큰 재발급 테스트
# ------------------------------
class TestTokenRefreshAPI(BaseTestCase):
    # @ns_auth.route('/refresh') 관련 테스트 2개
    # ** 토큰 재발급 성공 **
    def test_access_token_refresh_success(self):

        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                    content_type='application/json')
        refresh_token = json.loads(login_response.get_data(as_text=True))['refresh_token']

        headers = {
            'Authorization': f'Bearer {refresh_token}'
        }
        response = self.app.post('/auth/refresh', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        
        self.assertIn('access_token', data)
    
    # ** 리프레시 토큰 누락 **
    def test_token_refresh_without_token(self):

        response = self.app.post('/auth/refresh')
    
        self.assertEqual(response.status_code, 500)

# ------------------------------
#   사용자 CRUD 테스트
# ------------------------------
class TestUserAPI(BaseTestCase):
    # @ns_users.route('/') 관련 테스트 2개
    # ** 모든 사용자 조회 (관리자 권한 필요) **
    def test_all_get_users(self):
        login_data = {
            'id': 'A001',
            'password': '1234',
            'role': 'admin'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/users/', headers=headers)
        self.assertEqual(response.status_code, 200)

    # ** 모든 사용자 조회 실패 (권한 부족) **
    def test_get_all_users_failure(self):
        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/users/', headers=headers)
        self.assertEqual(response.status_code, 403)
    
    # @ns_users.route('/<id>') 관련 테스트 2개
    # ** 특정 사용자 조회 성공 **
    def test_get_specific_user_success(self):
        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/users/2020001', headers=headers)
        self.assertEqual(response.status_code, 200)
    
    # ** 특정 사용자 조회 실패 (존재하지 않는 사용자) **
    def test_get_specific_user_not_found(self):
        login_data = {
            'id': 'A001',
            'password': '1234',
            'role': 'admin'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/users/9999999', headers=headers)
        self.assertEqual(response.status_code, 404)


#------------------------------
#   과목 CRUD 테스트
# ------------------------------
class TestSubjectAPI(BaseTestCase):
    # @ns_subjects.route('/') 관련 테스트 2개
    # ** 모든 과목 조회 (관리자 권한 필요) **
    def test_get_all_subjects(self):
        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/subjects/', headers=headers)
        self.assertEqual(response.status_code, 200)

    # ** 과목 삽입 후 삭제 성공 테스트 (관리자 권한 필요) **
    def test_create_and_delete_subject_success(self):
        login_data = {
            'id': 'A001',
            'password': '1234',
            'role': 'admin'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                    content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        subject_data = {
            'code': 'CS101',
            'name': 'Introduction to Computer Science',
            'credits': 3,
            'professor_id': 'P001'
        }

        self.app.delete(f"/subjects/{subject_data['name']}", headers=headers)

        create_response = self.app.post('/subjects/', data=json.dumps(subject_data),
                                        content_type='application/json', headers=headers)
        
        self.assertEqual(create_response.status_code, 201)
        data = json.loads(create_response.get_data(as_text=True))
        self.assertEqual(data['code'], 'CS101')
        self.assertEqual(data['name'], 'Introduction to Computer Science')
        self.assertEqual(data['credits'], 3)
        self.assertEqual(data['professor_id'], 'P001')

        delete_response = self.app.delete(f"/subjects/{subject_data['name']}", headers=headers)
        
        self.assertEqual(delete_response.status_code, 204)
    
    # @ns_subjects.route('/<subject_name>') 관련 테스트 2개
    # ** 존재하는 과목에 접근 테스트 ** 
    def test_get_subject_success(self):
        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/subjects/C프로그래밍', headers=headers)
        data = json.loads(response.get_data(as_text=True))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['name'], 'C프로그래밍')

    # ** 존재하지 않는 과목에 접근 테스트 ** 
    def test_get_subject_not_found(self):
        login_data = {
            'id': '2020001',
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/subjects/wrongSubjectName', headers=headers)
        self.assertEqual(response.status_code, 404)
        
    # @ns_subjects.route('/professor/<professor_id>') 관련 테스트 2개
    # ** 교수 담당 과목 조회 성공 테스트 **
    def test_get_professor_subjects_success(self):
        login_data = {
            'id': 'P001',  
            'password': '1234',
            'role': 'professor'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = self.app.get('/subjects/professor/P001', headers=headers)
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        
        self.assertIsInstance(data, list) 
        for subject in data:
            self.assertEqual(subject['professor_id'], 'P001')  

    # ** 교수 담당 과목 조회 실패 (권한 부족) 테스트 **
    def test_get_professor_subjects_no_permission(self):
        login_data = {
            'id': '2020001',  
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        response = self.app.get('/subjects/professor/P001', headers=headers)
        
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        
        self.assertEqual(data['message'], "데이터에 접근 권한이 없습니다.")

#------------------------------
#   학생별 전체 성적 조회
# ------------------------------
class TestGradesAPI(BaseTestCase):
    # @ns_grades.route('/student/<student_id>') 관련 테스트 2개
    # ** 학생별 전체 성적 조회 성공 테스트 **
    def test_get_student_grades_success(self):
        login_data = {
            'id': '2020001',  
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/grades/student/2020001', headers=headers)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.get_data(as_text=True))
        self.assertTrue(len(data) > 0)  

    # ** 학생별 전체 성적 조회 실패 테스트 **
    def test_get_student_grades_no_permission(self):
        login_data = {
            'id': '2020001',  
            'password': '1234',
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/grades/student/19013139', headers=headers)

        self.assertEqual(response.status_code, 403)
        data = json.loads(response.get_data(as_text=True))
        self.assertEqual(data['message'], "데이터에 접근 권한이 없습니다.")

#------------------------------
#   과목별, 학기별 성적 조회
# ------------------------------
class TestSubjectGradesAPI(BaseTestCase):
    # @ns_grades.route('/subject/<subject_name>') 관련 테스트 2개
    # ** 과목별 성적 조회 성공 테스트 **
    def test_get_subject_grades_success(self):
        login_data = {
            'id': 'P001',
            'password': '1234', 
            'role': 'professor'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/grades/subject/C프로그래밍', headers=headers)

        self.assertEqual(response.status_code, 200)

    # ** 과목별 성적 조회 실패 테스트 **
    def test_get_subject_grades_not_found(self):
        login_data = {
            'id': 'A001', 
            'password': '1234', 
            'role': 'admin'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = self.app.get('/grades/subject/wrongSubjectName', headers=headers)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("해당 과목을 찾을 수 없습니다.", data['message'])
    
    # @ns_grades.route('/semester/<semester>') 관련 2개 테스트
    # ** 학기별 성적 조회 성공 테스트 **
    def test_get_semester_grades_success(self):
        login_data = {
            'id': '2020001', 
            'password': '1234', 
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = self.app.get('/grades/semester/2021-1', headers=headers)
        self.assertEqual(response.status_code, 200)

    # ** 학기별 성적 조회 실패 테스트 (성적 없음) **
    def test_get_semester_grades_not_found(self):
        login_data = {
            'id': '2020001', 
            'password': '1234', 
            'role': 'student'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        response = self.app.get('/grades/semester/2025-1', headers=headers)
        self.assertEqual(response.status_code, 404)

#------------------------------
#   성적 입력 테스트
# ------------------------------
class TestGradeCreationAPI(BaseTestCase):
    # @ns_grades.route('/') 관련 테스트 2개
    # ** 이미 입력된 성적으로 성적 입력 실패 테스트 **
    def test_add_grade_success(self):
        login_data = {
            'id': 'P001', 
            'password': '1234', 
            'role': 'professor'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        grade_data = {
            'student_id': '2020001',
            'subject_code': 'COMP101',
            'semester': '2020-1',
            'score': 3.0,
            'grade': 'B'
        }
        response = self.app.post('/grades/', data=json.dumps(grade_data),
                                 content_type='application/json', headers=headers)
                                 
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("해당 과목의 성적이 이미 존재합니다.", data['message'])

    # ** 권한 없음을 인한 성적 입력 실패 테스트 **
    def test_add_grade_duplicate(self):
        login_data = {
            'id': 'P001', 
            'password': '1234', 
            'role': 'professor'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        grade_data = {
            'student_id': '2020001',
            'subject_code': 'ELEC101',
            'semester': '2020-1',
            'score': 4.5,
            'grade': 'A+'
        }
        response = self.app.post('/grades/', data=json.dumps(grade_data),
                                 content_type='application/json', headers=headers)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("담당하지 않은 과목에 성적을 입력할 수 없습니다.", data['message'])

#------------------------------
#   성적 수정 테스트
# ------------------------------
class TestGradeUpdateAPI(BaseTestCase):
    # @ns_grades.route('/student/<string:student_id>/semester/<string:semester>/subject/<string:subject_code>') 관련 테스트 2개
    # ** 성적 수정 성공 테스트 **
    def test_update_grade_success(self):
        login_data = {
            'id': 'A001', 
            'password': '1234', 
            'role': 'admin'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        grade_data = {
            'score': 4, 
            'grade': 'A'
        }
        response = self.app.put('/grades/student/2020001/semester/2020-1/subject/COMP101', 
                                data=json.dumps(grade_data), content_type='application/json', headers=headers)
        self.assertEqual(response.status_code, 200)

    # ** 성적 수정 실패 테스트 (권한 없음) **
    def test_update_grade_no_permission(self):
        login_data = {
            'id': 'P001', 
            'password': '1234', 
            'role': 'professor'
        }
        login_response = self.app.post('/auth/login', data=json.dumps(login_data),
                                       content_type='application/json')
        access_token = json.loads(login_response.get_data(as_text=True))['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        grade_data = {
            'score': 4, 
            'grade': 'A'
        }
        response = self.app.put('/grades/student/2020001/semester/2020-1/subject/ELEC101', 
                                data=json.dumps(grade_data), content_type='application/json', headers=headers)
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.get_data(as_text=True))
        self.assertIn("담당하지 않은 과목의 성적을 수정할 수 없습니다.", data['message'])

if __name__ == '__main__': 
    unittest.main()
