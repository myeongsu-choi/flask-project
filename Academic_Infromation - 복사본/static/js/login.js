document.querySelector('.login-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const id = document.getElementById('id').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;

    const response = await fetch('/auth/login' , {
        method : 'POST',
        headers : {
            'Content-Type' : 'application/json'
        },
        body : JSON.stringify({id, password, role})
    });

    if (response.ok) {
        const data = await response.json();

        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user_id', data.user.id);
        localStorage.setItem('user_name', data.user.name);
        localStorage.setItem('user_role', data.user.role);
        
        window.location.href = '/dashboard';
    }
    else {
        const result = await response.json();
        alert(result.message || '로그인에 실패했습니다. 다시 시도해주세요.');
    }
});