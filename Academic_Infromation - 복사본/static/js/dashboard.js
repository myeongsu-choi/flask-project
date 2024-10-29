document.addEventListener('DOMContentLoaded', function() {
    const userRole = localStorage.getItem('user_role');
    const userName = localStorage.getItem('user_name'); 
    const roleDisplay = document.getElementById('role-display');
    const welcomeMessage = document.getElementById('welcome-message'); 
    const studentSection = document.getElementById('student-section');
    const gradesSection = document.getElementById('grades-section');
    const gradesList = document.getElementById('grades-list');
    
    if (userRole === 'admin') {
        roleDisplay.textContent = '관리자용';
        document.getElementById('admin-section').style.display = 'block';
    } else if (userRole === 'professor') {
        roleDisplay.textContent = '교수용';
        document.getElementById('professor-section').style.display = 'block';
    } else if (userRole === 'student') {
        roleDisplay.textContent = '학생용';
        document.getElementById('student-section').style.display = 'block';
    } else {
        alert("알 수 없는 사용자 역할입니다.");
    }
    welcomeMessage.textContent = `환영합니다! ${userName}님!`; 

    // 성적 조회 버튼 클릭 시 성적 데이터를 가져오는 요청
    document.getElementById('fetch-grades').addEventListener('click', async function() {
        const userId = localStorage.getItem('user_id');
        const accessToken = localStorage.getItem('access_token');

        try {
            const response = await fetch(`/grades/student/${userId}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            if (response.ok) {
                const grades = await response.json();
                gradesList.innerHTML = ''; // 이전 데이터 초기화
                gradesSection.style.display = 'block';

                // 학기별로 성적을 그룹화
                const gradesBySemester = grades.reduce((acc, grade) => {
                    const { semester } = grade;
                    if (!acc[semester]) acc[semester] = [];
                    acc[semester].push(grade);
                    return acc;
                }, {});

                // 학기별로 나열하여 HTML 생성
                Object.keys(gradesBySemester).forEach(semester => {
                    const semesterHeader = document.createElement('h4');
                    semesterHeader.textContent = `${semester} 학기`;
                    gradesList.appendChild(semesterHeader);

                    const semesterList = document.createElement('ul');
                    gradesBySemester[semester].forEach(grade => {
                        const listItem = document.createElement('li');
                        listItem.textContent = `${grade.subject_name}: ${grade.grade}`;
                        semesterList.appendChild(listItem);
                    });

                    gradesList.appendChild(semesterList);
                });
            } else {
                const errorData = await response.json();
                console.error("Error Data:", errorData);
                alert("성적을 불러오는 데 실패했습니다.");
            }
        } catch (error) {
            console.error("성적 조회 중 에러 발생:", error);
        }
    });

    document.getElementById('create-grades').addEventListener('click', function() {
        window.location.href = "/grades/create"; 
    });

    document.getElementById('manage-grades').addEventListener('click', function() {
        window.location.href = "/grades/manage"; // 성적 관리 페이지
    });

    document.getElementById('logout-button').addEventListener('click', function() {
        localStorage.clear(); // 모든 저장된 데이터 삭제
        window.location.href = "/login"; // 로그인 페이지로 리디렉션
    });

    document.getElementById('professor-logout-button').addEventListener('click', function() {
        localStorage.clear(); // 모든 저장된 데이터 삭제
        window.location.href = "/login"; // 로그인 페이지로 리디렉션
    });
});
