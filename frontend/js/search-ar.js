document.addEventListener('DOMContentLoaded', () => {
    const documents = [
        {
            title: 'المادة 123 - القانون المدني',
            text: 'نص المادة القانونية يظهر هنا مع تفاصيل إضافية عن محتواها وتطبيقها.',
            category: 'civil',
            categoryDisplay: 'القانون المدني',
            year: '2023',
            thumbnail: 'assets/images/thumbnails/civil law.png',
            url: 'assets/documents/civil-law-guide.pdf'
        },
        {
            title: 'المادة 45 - قانون الأسرة',
            text: 'وصف تفصيلي للمادة القانونية مع شرح لتطبيقها في الحالات المختلفة.',
            category: 'family',
            categoryDisplay: 'قانون الأسرة',
            year: '2022',
            thumbnail: 'assets/images/thumbnails/family-thumb.png',
            url: 'assets/documents/family-law-guide.pdf'
        },
        {
            title: 'المادة 78 - القانون التجاري',
            text: 'معلومات عن المادة القانونية وتأثيرها على المعاملات التجارية.',
            category: 'commercial',
            categoryDisplay: 'القانون التجاري',
            year: '2024',
            thumbnail: 'assets/images/thumbnails/business law.png',
            url: 'assets/documents/business-law-guide.pdf'
        },
        {
            title: 'المادة 32 - القانون الجنائي',
            text: 'تفاصيل حول الإجراءات الجنائية وحقوق المتهم.',
            category: 'criminal',
            categoryDisplay: 'القانون الجنائي',
            year: '2023',
            thumbnail: 'assets/images/thumbnails/criminal-thumb.png',
            url: 'assets/documents/criminal-law-guide.pdf'
        }
    ];

    const searchInput = document.getElementById('search-input');
    const categoryFilter = document.getElementById('category-filter');
    const yearFilter = document.getElementById('year-filter');
    const resultsContainer = document.querySelector('.search-results');

    function renderResults(filteredDocuments) {
        resultsContainer.innerHTML = '';

        if (filteredDocuments.length === 0) {
            resultsContainer.innerHTML = '<p class="lexend-deca-regular">لا توجد نتائج مطابقة لبحثك.</p>';
            return;
        }

        filteredDocuments.forEach(doc => {
            const resultCard = `
                <div class="result-card" data-category="${doc.category}" data-year="${doc.year}">
                    <div class="result-preview">
                        <img src="${doc.thumbnail}" alt="معاينة المستند" class="preview-thumbnail">
                        <div class="preview-overlay">
                            <a href="${doc.url}" download class="preview-download" aria-label="تحميل المستند">
                                <i class="fas fa-download"></i>
                            </a>
                        </div>
                    </div>
                    <div class="result-content">
                        <h3 class="result-title kufam-semibold">${doc.title}</h3>
                        <p class="result-text lexend-deca-regular">${doc.text}</p>
                        <div class="result-meta">
                            <span class="result-category lexend-deca-regular">${doc.categoryDisplay}</span>
                            <span class="result-year lexend-deca-regular">${doc.year}</span>
                            <a href="${doc.url}" download class="result-download lexend-deca-regular">
                                <i class="fas fa-download"></i>
                                تحميل
                            </a>
                        </div>
                    </div>
                </div>
            `;
            resultsContainer.insertAdjacentHTML('beforeend', resultCard);
        });
    }

    function filterAndRender() {
        const searchTerm = searchInput.value.toLowerCase();
        const selectedCategory = categoryFilter.value;
        const selectedYear = yearFilter.value;

        const filtered = documents.filter(doc => {
            const matchesCategory = !selectedCategory || doc.category === selectedCategory;
            const matchesYear = !selectedYear || doc.year === selectedYear;
            const matchesSearch = !searchTerm || doc.title.toLowerCase().includes(searchTerm) || doc.text.toLowerCase().includes(searchTerm);
            return matchesCategory && matchesYear && matchesSearch;
        });

        renderResults(filtered);
    }

    searchInput.addEventListener('input', filterAndRender);
    categoryFilter.addEventListener('change', filterAndRender);
    yearFilter.addEventListener('change', filterAndRender);

    // Initial render
    renderResults(documents);
}); 