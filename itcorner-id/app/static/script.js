// Script untuk Toggle Show/Hide Password
document.addEventListener('DOMContentLoaded', function () {
    // 1. Ambil elemen ikon mata dan input password berdasarkan ID-nya
    const togglePassword = document.querySelector('#togglePassword');
    const password = document.querySelector('#password');

    // 2. Pastikan elemennya ada di halaman sebelum menjalankan fungsi klik
    if (togglePassword && password) {
        togglePassword.addEventListener('click', function () {
            // 3. Cek tipe input: jika 'password' ubah jadi 'text', jika tidak kembalikan jadi 'password'
            const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
            password.setAttribute('type', type);
            
            // 4. Tambahkan atau hapus efek warna biru pada ikon saat aktif
            this.classList.toggle('text-blue-600');
        });
    }
});
// Script khusus untuk Register (2 Password Toggle)
document.addEventListener('DOMContentLoaded', function () {
    function setupRegisterToggle(toggleId, inputId) {
        const toggle = document.getElementById(toggleId);
        const input = document.getElementById(inputId);

        if (toggle && input) {
            toggle.addEventListener('click', function () {
                const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
                input.setAttribute('type', type);
                this.classList.toggle('text-blue-600');
            });
        }
    }

    // Jalankan untuk register
    setupRegisterToggle('togglePassword1', 'password');
    setupRegisterToggle('togglePassword2', 'confirm_password');
});