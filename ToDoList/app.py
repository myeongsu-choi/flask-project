from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 데이터베이스 설정
# username에는 생성한 사용자 계정명 입력
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://CHOI:0707@localhost/flask_todo_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# SQLAlchemy 객체 생성
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self): 
        return f'<Todo {self.title}>'

# Todo 항목들을 출력 / 페이지당 5개씩 출력
@app.route('/')
def index():
    page = request.args.get('page', 1, type = int)
    per_page = 5
    search_query = request.args.get('search', '')

    if search_query:
        todos = Todo.query.filter(Todo.title.contains(search_query)).paginate(page=page, per_page=per_page, error_out=False)
    else:
        todos = Todo.query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('index.html', todos = todos)

# 새로운 Todo 항목 추가
@app.route('/todo', methods = ['POST'])
def add_todo():
    title = request.form['title']
    description = request.form['description']
    
    new_todo = Todo(
        title = title,
        description = description
    )

    db.session.add(new_todo)
    db.session.commit()

    return redirect(url_for('index'))

# Todo 항목 완료/미완료 상태 변경
@app.route('/complete/<int:todo_id>', methods = ['POST'])
def complete(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.completed = not todo.completed
    db.session.commit()
    page = request.args.get('page', 1, type = int)
    return redirect(url_for('index', page=page))

# Todo 항목 삭제
@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()

    page = request.args.get('page', 1, type=int)
    return redirect(url_for('index', page = page))

# 수정할 Todo 항목의 수정 페이지 출력
@app.route('/edit_todo/<int:todo_id>', methods=['GET'])
def edit_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id) 
    page = request.args.get('page', 1, type=int)
    return render_template('edit_todo.html', todo=todo, page=page)

# 수정 페이지에서 입력을 완료하면 Todo 항목 업데이트
@app.route('/update_todo/<int:todo_id>', methods=['POST'])
def update_todo(todo_id):
    todo = Todo.query.get_or_404(todo_id)
    todo.title = request.form['title']
    todo.description = request.form['description']

    db.session.commit()
    page = request.args.get('page', 1, type=int)

    return redirect(url_for('index', page=page))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)