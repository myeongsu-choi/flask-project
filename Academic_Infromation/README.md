# 학사 정보 RESTful API

이 프로젝트는 Flask와 Flask-RESTx를 사용하여 학사 정보를 관리하는 RESTful API입니다. 사용자, 과목, 성적 데이터를 다룰 수 있으며, 인증과 역할 기반 접근 제어 기능이 포함되어 있습니다.

## 주요 기능
- **사용자 관리**: 학생, 교수, 관리자 사용자 정보의 CRUD (생성, 조회, 수정, 삭제) 기능
- **과목 관리**: 학사 과목 정보의 CRUD 기능
- **성적 관리**: 학생 성적 추가, 조회, 수정 기능
- **역할 기반 접근 제어**:
  - **학생**: 자신의 성적만 조회 가능
  - **교수**: 담당 과목의 성적 추가 및 수정 가능
  - **관리자**: 모든 사용자, 과목, 성적 데이터 관리 가능

## 기술 스택
- **백엔드**: Python, Flask, Flask-RESTx, Flask-SQLAlchemy
- **데이터베이스**: MySQL (PyMySQL을 통한 연결)
- **인증**: Flask-JWT-Extended를 이용한 JWT 기반 인증

## 설치 및 설정

### 1. 사전 요구 사항
- Python 3.8 이상
- MySQL 데이터베이스 서버

### 2. 코드 복제 및 패키지 설치

```bash

# 가상 환경 생성
python -m venv venv

# 필수 패키지 설치
pip install -r requirements.txt
```
### 3. 테스트 코드 실행 방법
```bash
python test.py
```
