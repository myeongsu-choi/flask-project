async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if(!refreshToken) {
        console.log('Refresh token이 없습니다.');
        return;
    }

    const response = await fetch('/auth/refresh', {
        method : 'POST',
        headers : {
            'Authorization' : `Bearer ${refreshToken}`
        }
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access_token)
        console.log("엑세스 토큰이 갱신되었습니다.");
    }
    else {
        console.log('토큰 갱신 실패');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 14분(840,000ms)마다 토큰 갱신
    setInterval(refreshAccessToken, 14 * 60 * 1000);
});