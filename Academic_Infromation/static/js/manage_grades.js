document.addEventListener('DOMContentLoaded', function() {
    const accessToken = localStorage.getItem('access_token');

    // 성적 조회 버튼 클릭 시 성적 데이터 가져오기
    document.getElementById('fetch-grades-button').addEventListener('click', async function() {
        const semester = document.getElementById('semester-select').value;

        try {
            const response = await fetch(`/grades/semester/${semester}`, {
                method: 'GET',
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });

            if (response.ok) {
                const grades = await response.json();
                displayGrades(grades);
            } else {
                alert("성적 조회에 실패했습니다.");
            }
        } catch (error) {
            console.error("성적 조회 중 오류 발생:", error);
        }
    });

    // 성적 리스트를 화면에 표시하는 함수
    function displayGrades(grades) {
        const gradesList = document.getElementById('grades-list');
        gradesList.innerHTML = '';
        
        grades.forEach(grade => {
            const listItem = document.createElement('li');
            listItem.textContent = `${grade.subject_name} (${grade.subject_code}) - 점수: ${grade.score}, 학점: ${grade.grade}`;
            listItem.addEventListener('click', () => editGrade(grade));
            gradesList.appendChild(listItem);
        });
    }

    // 성적 수정 화면에 데이터 로드
    function editGrade(grade) {
        document.getElementById('edit-score').value = grade.score;
        document.getElementById('edit-grade').value = grade.grade;
        document.getElementById('edit-grade-container').style.display = 'block';

        document.getElementById('edit-grade-form').onsubmit = async function(event) {
            event.preventDefault();
            await updateGrade(grade.student_id, grade.semester, grade.subject_code);
        };
    }

    // 성적 수정 요청
    async function updateGrade(studentId, semester, subjectCode) {
        const score = document.getElementById('edit-score').value;
        const grade = document.getElementById('edit-grade').value;

        try {
            const response = await fetch(`/grades/student/${studentId}/semester/${semester}/subject/${subjectCode}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({ score, grade })
            });

            if (response.ok) {
                alert("성적이 성공적으로 수정되었습니다.");
                document.getElementById('edit-grade-container').style.display = 'none';
                document.getElementById('edit-grade-form').reset();
            } else {
                alert("성적 수정에 실패했습니다.");
            }
        } catch (error) {
            console.error("성적 수정 중 오류 발생:", error);
        }
    }
});
