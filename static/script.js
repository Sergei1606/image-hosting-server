/**
 * Основной клиентский скрипт для сервиса хостинга изображений.
 *
 * Обеспечивает взаимодействие с пользователем и API бэкенда:
 * - Загрузка файлов через drag & drop
 * - Отображение списка загруженных изображений
 * - Навигация между вкладками
 * - Взаимодействие с Python бэкендом через REST API
 */

/**
 * Основной клиентский скрипт для сервиса хостинга изображений.
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

    const heroImages = [
        'static/assets/images/bird.png',
        'static/assets/images/cat.png',
        'static/assets/images/dog1.png',
        'static/assets/images/dog2.png',
        'static/assets/images/dog3.png'
    ];

    let uploadedImages = [];
    let originalContent = dropZone.innerHTML; // Сохраняем оригинальное содержимое

    // Загружаем сохраненные изображения из LocalStorage
    try {
        const savedImages = localStorage.getItem('uploadedImages');
        if (savedImages) {
            uploadedImages = JSON.parse(savedImages);
            console.log('Загружено изображений из LocalStorage:', uploadedImages.length);
        }
    } catch (error) {
        console.error('Ошибка загрузки из LocalStorage:', error);
    }

    // Функция для сохранения массива в LocalStorage
    function saveToLocalStorage() {
        try {
            localStorage.setItem('uploadedImages', JSON.stringify(uploadedImages));
            console.log('Сохранено в LocalStorage:', uploadedImages.length, 'изображений');
        } catch (error) {
            console.error('Ошибка сохранения в LocalStorage:', error);
        }
    }

    function setRandomHeroImage() {
        const randomIndex = Math.floor(Math.random() * heroImages.length);
        const randomImage = heroImages[randomIndex];
        heroPage.style.backgroundImage = `url(${randomImage})`;
    }

    gotoAppButton.addEventListener('click', () => {
        heroPage.classList.add('hidden');
        mainAppPage.classList.remove('hidden');

        if (uploadedImages.length > 0) {
            renderImages();
        }
    });

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const view = button.dataset.view;
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            if (view === 'upload') {
                uploadView.classList.remove('hidden');
                imagesView.classList.add('hidden');
            } else {
                uploadView.classList.add('hidden');
                imagesView.classList.remove('hidden');
                renderImages();
            }
        });
    });

    async function handleFileUpload(file) {
        console.log('=== НАЧАЛО ЗАГРУЗКИ ===');
        console.log('Файл:', file.name, 'Размер:', file.size);

        urlInput.value = '';
        uploadError.classList.add('hidden');

        originalContent = dropZone.innerHTML; // Обновляем оригинальное содержимое
        dropZone.innerHTML = '<i class="fas fa-spinner fa-spin"></i><p>Загрузка...</p>';

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('🔄 Отправляю запрос на сервер...');
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            console.log('✅ Ответ получен. Статус:', response.status);
            console.log('✅ Ответ OK?:', response.ok);

            const result = await response.json();
            console.log('📨 Данные от сервера:', result);

            if (response.status === 200 && result.status === 'success') {
                console.log('🎉 УСПЕХ! Файл загружен');

                const fullUrl = window.location.origin + result.url;
                urlInput.value = fullUrl;

                uploadedImages.push({
                    id: Date.now(),
                    name: file.name,
                    url: result.url,
                    originalName: result.original_name || file.name,
                    filename: result.filename
                });

                saveToLocalStorage();

                dropZone.innerHTML = originalContent;
                uploadError.textContent = 'Файл успешно загружен!';
                uploadError.style.color = 'green';
                uploadError.classList.remove('hidden');
                uploadError.style.display = 'block';

            } else {
                console.log('❌ ОШИБКА СЕРВЕРА:', result.message);

                // ВРЕМЕННЫЙ ALERT (можно поменять позже)
                alert(`🚨 СЕРВЕР ВЕРНУЛ ОШИБКУ:

Сообщение: ${result.message}
Статус: ${response.status}
Файл: ${file.name}
Размер: ${file.size} байт

Проверьте консоль (F12) для деталей`);

                // Показываем ошибку в интерфейсе
                uploadError.textContent = result.message;
                uploadError.classList.remove('hidden');
                uploadError.style.display = 'block';
                uploadError.style.color = 'red';
                uploadError.style.backgroundColor = '#ffeeee';
                uploadError.style.padding = '10px';
                uploadError.style.border = '2px solid red';
                uploadError.style.borderRadius = '5px';
                uploadError.style.margin = '10px 0';
                uploadError.style.fontWeight = 'bold';

                dropZone.innerHTML = originalContent;
            }

        } catch (error) {
            console.error('💥 СЕТЕВАЯ ОШИБКА:', error);

            // ✅ ОБРАБОТКА ОШИБОК: Определяем тип ошибки
            let errorMessage = 'Ошибка сети';
            // Проверяем тип сетевой ошибки
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                errorMessage = 'Сервер недоступен. Проверьте подключение.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'Запрос был отменен';
            }

            // ALERT для сетевых ошибок
            alert(`💥 СЕТЕВАЯ ОШИБКА:

Ошибка: ${error.message}
Файл: ${file.name}

Возможно, файл слишком большой или проблемы с соединением`);

            // Показываем ошибку в интерфейсе
            uploadError.textContent = errorMessage;
            uploadError.classList.remove('hidden');
            uploadError.style.display = 'block';
            uploadError.style.color = 'red';
            uploadError.style.backgroundColor = '#ffeeee';

            // Восстанавливаем dropZone
            dropZone.innerHTML = originalContent;
        }

        console.log('=== КОНЕЦ ЗАГРУЗКИ ===');
    }

    browseBtn.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

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

    copyBtn.addEventListener('click', async () => {
        if (urlInput.value) {
            try {
                await navigator.clipboard.writeText(urlInput.value);
                copyBtn.textContent = 'СКОПИРОВАНО!';
                setTimeout(() => {
                    copyBtn.textContent = 'КОПИРОВАТЬ';
                }, 2000);
            } catch (err) {
                console.error('Ошибка копирования:', err);
                urlInput.select();
                document.execCommand('copy');
            }
        }
    });

    function renderImages() {
        imageList.innerHTML = '';

        if (uploadedImages.length === 0) {
            imageList.innerHTML = `
                <p style="text-align:center; color: var(--text-muted); padding: 20px;">
                    Изображения еще не загружены.
                </p>
            `;
            return;
        }

        uploadedImages.forEach(image => {
            const templateClone = imageItemTemplate.content.cloneNode(true);

            templateClone.querySelector('.image-item').dataset.id = image.id;
            const nameSpan = templateClone.querySelector('.image-item__name span');
            nameSpan.textContent = image.originalName || image.name;

            const urlLink = templateClone.querySelector('.image-item__url a');
            urlLink.href = image.url;
            urlLink.textContent = image.url;
            urlLink.target = '_blank';
            urlLink.rel = 'noopener noreferrer';

            imageList.appendChild(templateClone);
        });
    }

    // Обработчик кликов по списку изображений
    imageList.addEventListener('click', async (e) => {
        // Обработка клика по ссылке (открытие изображения)
        const link = e.target.closest('a');
        if (link) {
            e.preventDefault();
            window.open(link.href, '_blank');
            return;
        }

        // Обработка удаления изображения
        const deleteButton = e.target.closest('.delete-btn');
        if (deleteButton) {
            const listItem = e.target.closest('.image-item');
            const imageId = parseInt(listItem.dataset.id, 10);

            // Находим изображение для удаления
            const imageToDelete = uploadedImages.find(img => img.id === imageId);
            if (!imageToDelete) return;

            try {
                // Отправляем запрос на удаление файла с сервера
                const response = await fetch(`/images/${imageToDelete.filename}`, {
                    method: 'DELETE'
                });

                const result = await response.json();

                if (result.status === 'success') {
                    // Удаляем изображение из массива
                    uploadedImages = uploadedImages.filter(img => img.id !== imageId);

                    // Сохраняем изменения в LocalStorage
                    saveToLocalStorage();

                    // Обновляем список
                    renderImages();

                    console.log('Файл успешно удален с сервера:', imageToDelete.filename);
                } else {
                    console.error('Ошибка удаления файла с сервера:', result.message);
                    alert('Ошибка при удалении файла: ' + result.message);
                }

            } catch (error) {
                console.error('Ошибка при удалении файла:', error);
                alert('Ошибка при удалении файла: ' + error.message);
            }
        }
    });

    setRandomHeroImage();

    if (uploadedImages.length > 0) {
        console.log('Рендерим сохраненные изображения:', uploadedImages.length);
        renderImages();
    }
});