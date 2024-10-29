document.addEventListener('DOMContentLoaded', function() {
    const userRole = localStorage.getItem('user_role');
    const userName = localStorage.getItem('user_name'); 
    
    const roleDisplay = document.getElementById('role-display');
    const gradesSection = document.getElementById('grades-section');
    const gradesList = document.getElementById('grades-list');

    let wellcomeMessage;
    
    /*
        사용자의 역할에 따라 따른 내용 표시
    */
    if (userRole === 'admin') {
        roleDisplay.textContent = '관리자용';
        document.getElementById('admin-section').style.display = 'block';
    } else if (userRole === 'professor') {
        roleDisplay.textContent = '교수용';
        document.getElementById('professor-section').style.display = 'block';
        wellcomeMessage = document.getElementById('professor-wellcome-message');
    } else if (userRole === 'student') {
        roleDisplay.textContent = '학생용';
        document.getElementById('student-section').style.display = 'block';
        wellcomeMessage = document.getElementById('student-wellcome-message');
    } else {
        alert("알 수 없는 사용자 역할입니다.");
    }

    if(wellcomeMessage)
        wellcomeMessage.textContent = `환영합니다! ${userName}님!`; 

    /*
        학생이 자신의 성적을 조회할 경우
    */
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

                gradesList.innerHTML = ''; 
                gradesSection.style.display = 'block';

                /*
                    grades 배열의 각 항목(grade)을 학기(semester)별로 그룹화하여,
                    학기를 키(key)로 가지는 객체 gradeBySemester를 생성한다.
                */
                const gradesBySemester = grades.reduce((acc, grade) => {
                    const { semester } = grade; // grade 객체에서 semester 속성만 추출하여 semester 변수에 할당
                    if (!acc[semester]) acc[semester] = []; // acc[semester] 가 존재하지 않는다면 빈 배열로 초기화
                    acc[semester].push(grade); // acc[semester] 배열에 grade 객체 추가
                    return acc;
                }, {});

                /*
                    gradesBySemester 객체에 저장된 학기별 성적 데이터를 HTML로 변환
                */
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
                alert(errorData.message || "성적을 불러오는 데 실패했습니다.")
            }
        } catch (error) {
            console.error("성적 조회 중 에러 발생:", error);
        }
    });

    document.getElementById('create-grades').addEventListener('click', function() {
        window.location.href = "/grades/create"; 
    });

    document.getElementById('manage-grades').addEventListener('click', function() {
        window.location.href = "/grades/manage"; 
    });

    document.getElementById('logout-button').addEventListener('click', function() {
        localStorage.clear(); 
        window.location.href = "/login";
    });

    document.getElementById('professor-logout-button').addEventListener('click', function() {
        localStorage.clear(); 
        window.location.href = "/login"; ㄴ
    });
});
