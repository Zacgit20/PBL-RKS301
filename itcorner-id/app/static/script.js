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
// penambahan script untuk menambahkan produk ke keranjang
let totalKeranjang = 0;

function tambahKeKeranjang(namaProduk) {
    totalKeranjang++;

    // Update angka di navbar secara otomatis
    const badgeCount = document.getElementById('cart-count');
    if (badgeCount) {
        badgeCount.innerText = totalKeranjang;
    }

    alert(namaProduk + " berhasil ditambahkan ke keranjang!");
}

// AGAR CART TIDAK REALOD JIKA DI KLIK +
function addToCart(event, formElement) {
    event.preventDefault(); // Mencegah reload halaman

    const formData = new FormData(formElement);

    fetch("/add-to-cart", {
        method: "POST",
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Gagal menambahkan produk.");
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            const cartBadge = document.getElementById("cart-count");
            if (cartBadge) {
                cartBadge.innerText = data.cart_count;
            }
        }
    })
    .catch(error => console.error("Error:", error));
}

// Fungsi untuk menambah/mengurangi jumlah produk di halaman cart
function updateCartQuantity(productId, action) {
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('action', action);

    fetch('/update-cart', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Gagal mengupdate keranjang");
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            window.location.reload(); // Refresh halaman untuk memperbarui total harga
        }
    })
    .catch(error => console.error("Error:", error));
}

// Fungsi untuk menghapus produk dari keranjang
function removeFromCart(productId) {
    const formData = new FormData();
    formData.append('product_id', productId);

    fetch('/remove-from-cart', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error("Gagal menghapus produk");
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            window.location.reload(); // Refresh halaman setelah hapus
        }
    })
    .catch(error => console.error("Error:", error));
}
// Preview gambar produk pada halaman Admin
document.addEventListener('DOMContentLoaded', function () {
    const imageInput = document.getElementById('product-image');
    const imagePreview = document.getElementById('image-preview');
    const placeholder = document.getElementById('preview-placeholder');

    // Pastikan elemen tersedia di halaman
    if (!imageInput || !imagePreview || !placeholder) {
        return;
    }

    let currentPreviewUrl = null;

    imageInput.addEventListener('change', function () {
        const file = this.files[0];

        if (!file) {
            return;
        }

        // Memeriksa tipe file
        const allowedTypes = [
            'image/jpeg',
            'image/png',
            'image/webp'
        ];

        if (!allowedTypes.includes(file.type)) {
            alert('Format gambar harus JPG, PNG, atau WebP.');
            this.value = '';
            return;
        }

        // Memeriksa ukuran file maksimal 2 MB
        if (file.size > 2 * 1024 * 1024) {
            alert('Ukuran gambar maksimal 2 MB.');
            this.value = '';
            return;
        }

        // Menghapus URL preview sebelumnya
        if (currentPreviewUrl) {
            URL.revokeObjectURL(currentPreviewUrl);
        }

        // Membuat URL sementara untuk menampilkan gambar
        currentPreviewUrl = URL.createObjectURL(file);

        imagePreview.src = currentPreviewUrl;
        imagePreview.classList.remove('hidden');
        placeholder.classList.add('hidden');
    });
});