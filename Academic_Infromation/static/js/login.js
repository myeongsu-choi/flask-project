document.querySelector('.login-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    /*
        form 제출에 사용된 데이터들을 가져와서 저장.
        - id : 사용자의 아이디
        - password : 사용자의 비밀번호
        - role : 사용자의 역할 (예: admin, student, professor)
    */
    const id = document.getElementById('id').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    /*
        로그인 요청을 위한 fetch 함수로 서버에 POST 요청을 전송
        - URL: /auth/login
        - method: 'POST' 방식으로 요청을 전송
        - headers: 요청이 JSON 형식임을 지정
        - body: id, password, role을 JSON 형식으로 변환하여 요청 본문에 포함
    */
    const response = await fetch('/auth/login' , {
        method : 'POST',
        headers : {
            'Content-Type' : 'application/json'
        },
        body : JSON.stringify({id, password, role})
    });

    /*
        서버 응답이 성공적일 경우
        - 서버에서 반환된 JWT 토큰과 사용자 정보를 로컬 스토리지에 저장
        - 이후 사용자 대시보드로 이동
    */
    if (response.ok) {
        const data = await response.json();

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_id', data.user.id);
        localStorage.setItem('user_name', data.user.name);
        localStorage.setItem('user_role', data.user.role);
        
        console.log("로그인 응답 데이터 : ", data);
        window.location.href = '/dashboard';
    }
    else {
        /*
            서버에서 반환된 오류 메시지를 JSON 형식으로 추출하여 경고창에 표시
        */
        const result = await response.json();
        alert(result.message || '로그인에 실패했습니다. 다시 시도해주세요.');
    }
});