document.addEventListener('DOMContentLoaded', function() { 
    const userName = localStorage.getItem('user_name'); 
    const roleDisplay = document.getElementById('role-display');

    roleDisplay.textContent = '교수용';

    document.getElementById('grade-form').addEventListener('submit', async function(event) {
        event.preventDefault();

        const studentId = document.getElementById('student_id').value;
        const subjectCode = document.getElementById('subject_code').value;
        const subjectName = document.getElementById('subject_name').value;
        const semester = document.getElementById('semester').value;
        const score = document.getElementById('score').value;
        const grade = document.getElementById('grade').value;
        const accessToken = localStorage.getItem('access_token');

        try {
            const response = await fetch('/grades', {
                method: 'POST',
                headers: {
                    'Content-Type' : 'application/json',
                    'Authorization' : `Bearer ${accessToken}`
                },
                body: JSON.stringify({
                    student_id: studentId,
                    subject_code: subjectCode,
                    subject_name: subjectName,
                    semester: semester,
                    score: score,
                    grade: grade
                })
            });

            if (response.ok) {
                alert("성적이 성공적으로 입력되었습니다.");
                document.getElementById('grade-form').reset();
            } else {
                const errorData = await response.json();
                alert(errorData.message || "성적 입력에 실패했습니다.");
            }
        } catch (error) {
            console.error("성적 입력 중 오류 발생:", error);
            alert("성적 입력에 실패했습니다.");
        }
    });
});