/**
 * ОБНОВЛЕННЫЙ клиентский скрипт для главной страницы
 * Адаптирован под вашу HTML структуру
 */
document.addEventListener('DOMContentLoaded', () => {
    const heroPage = document.getElementById('hero-page');
    const mainAppPage = document.getElementById('main-app-page');
    const gotoAppButton = document.getElementById('goto-app-button');
    const navButtons = document.querySelectorAll('.app-nav__button');
    const uploadView = document.getElementById('upload-view');
    const imagesView = document.getElementById('images-view');
    const dropZone = document.getElementById('upload-drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const uploadError = document.getElementById('upload-error');
    const urlInput = document.getElementById('url-input');
    const copyBtn = document.getElementById('copy-btn');
    const imageList = document.getElementById('image-list');
    const imageItemTemplate = document.getElementById('image-item-template');

    // 🔥 РАНДОМНЫЕ КАРТИНКИ ДЛЯ ГЛАВНОЙ СТРАНИЦЫ
    const heroImages = [
        '/static/images/bird.png',
        '/static/images/cat.png',
        '/static/images/dog1.png',
        '/static/images/dog2.png',
        '/static/images/dog3.png'
    ];

    let originalContent = dropZone.innerHTML;

    // 🔥 ОСНОВНАЯ ФУНКЦИЯ - загрузка изображений с сервера
    async function loadImagesFromServer() {
        try {
            console.log('🔄 Загружаем изображения с сервера...');
            const response = await fetch('/images-list-data');

            if (!response.ok) {
                throw new Error(`Ошибка сервера: ${response.status}`);
            }

            const serverImages = await response.json();
            console.log('✅ Загружено изображений с сервера:', serverImages.length);

            return serverImages.map(img => ({
                id: img.id,
                filename: img.filename,
                url: `/images/${img.filename}`,
                originalName: img.original_name,
                size: img.size,
                uploadTime: img.upload_time,
                fileType: img.file_type
            }));

        } catch (error) {
            console.error('💥 Ошибка загрузки изображений:', error);
            showNotification('❌ Ошибка загрузки изображений: ' + error.message, 'error');
            return [];
        }
    }

    // 🔥 ОТОБРАЖЕНИЕ ИЗОБРАЖЕНИЙ ИЗ ДАННЫХ СЕРВЕРА
    async function renderImages() {
        try {
            const images = await loadImagesFromServer();
            imageList.innerHTML = '';

            if (images.length === 0) {
                imageList.innerHTML = `
                    <li style="text-align:center; color: var(--text-muted); padding: 40px; list-style: none;">
                        <i class="fas fa-image" style="font-size: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
                        <p>Изображения еще не загружены.</p>
                        <p style="font-size: 0.9em; margin-top: 8px;">Загрузите первое изображение на вкладке "Загрузить"</p>
                    </li>
                `;
                return;
            }

            images.forEach(image => {
                const templateClone = imageItemTemplate.content.cloneNode(true);
                const imageItem = templateClone.querySelector('.image-item');

                // 🔥 Используем реальный ID из базы данных
                imageItem.dataset.id = image.id;
                imageItem.dataset.filename = image.filename;

                // Заполняем имя файла
                const nameSpan = templateClone.querySelector('.image-item__name span');
                nameSpan.textContent = image.originalName;

                // Заполняем ссылку
                const urlLink = templateClone.querySelector('.image-item__url a');
                urlLink.href = image.url;
                urlLink.textContent = image.url;

                // Добавляем информацию о размере и дате
                const sizeInKB = (image.size / 1024).toFixed(1);
                const uploadDate = new Date(image.uploadTime).toLocaleString('ru-RU');

                const infoDiv = document.createElement('div');
                infoDiv.style.cssText = 'font-size: 0.8em; color: #666; margin-top: 5px;';
                infoDiv.innerHTML = `
                    <span>${sizeInKB} KB</span> •
                    <span>${uploadDate}</span> •
                    <span>${image.fileType}</span>
                `;

                nameSpan.parentNode.appendChild(infoDiv);

                imageList.appendChild(templateClone);
            });

            console.log('✅ Отрисовано изображений:', images.length);

        } catch (error) {
            console.error('💥 Ошибка отрисовки изображений:', error);
            imageList.innerHTML = `
                <li style="text-align:center; color: #e53e3e; padding: 20px; list-style: none;">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Ошибка загрузки изображений</p>
                </li>
            `;
        }
    }

    // 🔥 ФУНКЦИЯ УДАЛЕНИЯ ИЗОБРАЖЕНИЯ
    async function deleteImage(imageId, filename) {
        if (!confirm(`Вы уверены, что хотите удалить изображение "${filename}"?`)) {
            return;
        }

        try {
            console.log('🔄 Удаляем изображение ID:', imageId);
            const response = await fetch(`/delete/${imageId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (result.status === 'success') {
                console.log('✅ Изображение успешно удалено');
                showNotification('✅ Изображение успешно удалено', 'success');

                // Перезагружаем список
                await renderImages();
            } else {
                console.error('❌ Ошибка удаления:', result.message);
                showNotification('❌ Ошибка при удалении: ' + result.message, 'error');
            }
        } catch (error) {
            console.error('💥 Ошибка при удалении:', error);
            showNotification('💥 Ошибка при удалении: ' + error.message, 'error');
        }
    }

    // 🔥 ФУНКЦИЯ ЗАГРУЗКИ ФАЙЛА
    async function handleFileUpload(file) {
        console.log('=== НАЧАЛО ЗАГРУЗКИ ===');
        console.log('Файл:', file.name, 'Размер:', file.size);

        urlInput.value = '';
        uploadError.classList.add('hidden');

        // Показываем индикатор загрузки
        const originalContent = dropZone.innerHTML;
        dropZone.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Загрузка...</p>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('🔄 Отправляем файл на сервер...');
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            console.log('✅ Ответ получен. Статус:', response.status);
            const result = await response.json();
            console.log('📨 Данные от сервера:', result);

            if (response.ok && result.status === 'success') {
                console.log('🎉 Файл успешно загружен!');

                const fullUrl = window.location.origin + result.url;
                urlInput.value = fullUrl;

                // Показываем успех
                dropZone.innerHTML = originalContent;
                uploadError.textContent = '✅ Файл успешно загружен!';
                uploadError.style.color = 'green';
                uploadError.classList.remove('hidden');

                showNotification('✅ Изображение успешно загружено', 'success');

                // Автоматически переключаемся на вкладку изображений и обновляем список
                setTimeout(async () => {
                    navButtons.forEach(btn => btn.classList.remove('active'));
                    document.querySelector('[data-view="images"]').classList.add('active');
                    uploadView.classList.add('hidden');
                    imagesView.classList.remove('hidden');
                    await renderImages();
                }, 1500);

            } else {
                throw new Error(result.message || 'Неизвестная ошибка сервера');
            }

        } catch (error) {
            console.error('💥 Ошибка загрузки:', error);

            // Восстанавливаем dropZone
            dropZone.innerHTML = originalContent;

            // Показываем ошибку
            uploadError.textContent = '❌ ' + error.message;
            uploadError.style.color = 'red';
            uploadError.classList.remove('hidden');

            showNotification('❌ Ошибка загрузки: ' + error.message, 'error');
        }

        console.log('=== КОНЕЦ ЗАГРУЗКИ ===');
    }
    // 🔥 ОБРАБОТЧИКИ СОБЫТИЙ
    function setupEventListeners() {
        // Навигация
        gotoAppButton.addEventListener('click', () => {
            heroPage.classList.add('hidden');
            mainAppPage.classList.remove('hidden');
        });

        navButtons.forEach(button => {
            button.addEventListener('click', async () => {
                const view = button.dataset.view;
                navButtons.forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');

                if (view === 'upload') {
                    uploadView.classList.remove('hidden');
                    imagesView.classList.add('hidden');
                } else {
                    // 🔥  ПЕРЕНАПРАВЛЯЕМ НА /images-list
                    window.location.href = '/images-list';
                }
            });
        });

//        // Загрузка файлов
        browseBtn.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFileUpload(fileInput.files[0]);
            }
        });

        // Drag & Drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });

        // Копирование URL
        copyBtn.addEventListener('click', async () => {
            if (urlInput.value) {
                try {
                    await navigator.clipboard.writeText(urlInput.value);
                    copyBtn.innerHTML = '<i class="fas fa-check"></i> СКОПИРОВАНО!';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<i class="fas fa-copy"></i> КОПИРОВАТЬ';
                    }, 2000);
                } catch (err) {
                    console.error('Ошибка копирования:', err);
                    urlInput.select();
                    document.execCommand('copy');
                }
            }
        });

        // Обработчик удаления изображений
        imageList.addEventListener('click', async (e) => {
            const link = e.target.closest('a');
            if (link) {
                e.preventDefault();
                window.open(link.href, '_blank');
                return;
            }

            const deleteButton = e.target.closest('.delete-btn');
            if (deleteButton) {
                const listItem = e.target.closest('.image-item');
                const imageId = parseInt(listItem.dataset.id, 10);
                const filename = listItem.dataset.filename;

                await deleteImage(imageId, filename);
            }
        });
    }

    // 🔥 ФУНКЦИЯ УВЕДОМЛЕНИЙ
    function showNotification(message, type = 'info') {
        document.querySelectorAll('.notification').forEach(notif => notif.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'exclamation-triangle' : 'info'}"></i>
                <span>${message}</span>
            </div>
        `;

        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#4299e1'};
            color: white;
            border-radius: 8px;
            z-index: 10000;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            max-width: 400px;
            cursor: pointer;
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);

        notification.addEventListener('click', () => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        });
    }

    // 🔥 ИНИЦИАЛИЗАЦИЯ
    function init() {
        // Добавляем CSS анимации
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .notification {
                transition: transform 0.2s ease;
            }
            .notification:hover {
                transform: scale(1.02);
            }
        `;
        document.head.appendChild(style);

        // 🔥 УСТАНАВЛИВАЕМ СЛУЧАЙНОЕ ФОНОВОЕ ИЗОБРАЖЕНИЕ ДЛЯ ГЛАВНОЙ СТРАНИЦЫ
        function setRandomHeroImage() {
            const randomIndex = Math.floor(Math.random() * heroImages.length);
            const randomImage = heroImages[randomIndex];
            heroPage.style.backgroundImage = `url(${randomImage})`;
            console.log('🎨 Установлен фон:', randomImage);
        }

        // 🔥 ВЫЗЫВАЕМ ФУНКЦИЮ УСТАНОВКИ ФОНА
        setRandomHeroImage();

        // Настраиваем обработчики событий
        setupEventListeners();

        console.log('🚀 Приложение инициализировано');
    }

    // Запускаем приложение
    init();
});