// Language translations
const translations = {
    en: {
        // Search Page
        searchTitle: "Explore Legal Insights with Our Powerful Search Tool",
        searchDescription: "Search through our comprehensive database of legal documents, cases, and resources",
        searchPlaceholder: "Enter your search query...",
        searchButton: "Search",
        documentCategories: {
            familyLaw: "Family Law",
            criminalLaw: "Criminal Law",
            businessLaw: "Business Law",
            civilLaw: "Civil Law",
            employmentLaw: "Employment Law",
            administrativeLaw: "Administrative Law"
        },
        documentDescriptions: {
            familyLaw: "Family law documents, marriage contracts, and divorce proceedings",
            criminalLaw: "Criminal cases, legal procedures, and rights",
            businessLaw: "Business contracts, corporate law, and commercial regulations",
            civilLaw: "Civil cases, property rights, and personal disputes",
            employmentLaw: "Employment contracts, labor rights, and workplace regulations",
            administrativeLaw: "Administrative procedures, government regulations, and public law"
        },
        downloadButton: "Download",
        noResults: "No results found. Try different keywords.",
        loadingResults: "Loading results...",
        errorMessage: "An error occurred. Please try again."
    },
    ar: {
        // Search Page
        searchTitle: "استكشف الرؤى القانونية باستخدام أداة البحث القوية",
        searchDescription: "ابحث في قاعدة بياناتنا الشاملة للوثائق القانونية والقضايا والموارد",
        searchPlaceholder: "أدخل استعلام البحث...",
        searchButton: "بحث",
        documentCategories: {
            familyLaw: "قانون الأسرة",
            criminalLaw: "القانون الجنائي",
            businessLaw: "قانون الأعمال",
            civilLaw: "القانون المدني",
            employmentLaw: "قانون العمل",
            administrativeLaw: "القانون الإداري"
        },
        documentDescriptions: {
            familyLaw: "وثائق قانون الأسرة وعقود الزواج وإجراءات الطلاق",
            criminalLaw: "القضايا الجنائية والإجراءات القانونية والحقوق",
            businessLaw: "عقود الأعمال وقانون الشركات واللوائح التجارية",
            civilLaw: "القضايا المدنية وحقوق الملكية والنزاعات الشخصية",
            employmentLaw: "عقود العمل وحقوق العمال ولوائح مكان العمل",
            administrativeLaw: "الإجراءات الإدارية واللوائح الحكومية والقانون العام"
        },
        downloadButton: "تحميل",
        noResults: "لم يتم العثور على نتائج. جرب كلمات مفتاحية مختلفة.",
        loadingResults: "جاري تحميل النتائج...",
        errorMessage: "حدث خطأ. يرجى المحاولة مرة أخرى."
    }
};

// Function to update language
function updateLanguage(lang) {
    // Get the current page
    const currentPage = window.location.pathname.split('/').pop();

    // Only update search page
    if (currentPage === 'search-page.html') {
        // Update search section
        const searchTitle = document.querySelector('.search-content h1');
        const searchDescription = document.querySelector('.search-content p');
        const searchInput = document.querySelector('.search-input');
        const searchButton = document.querySelector('.search-button');

        if (searchTitle) searchTitle.textContent = translations[lang].searchTitle;
        if (searchDescription) searchDescription.textContent = translations[lang].searchDescription;
        if (searchInput) searchInput.placeholder = translations[lang].searchPlaceholder;
        if (searchButton) searchButton.textContent = translations[lang].searchButton;

        // Update document cards
        const documentCards = document.querySelectorAll('.document-card');
        documentCards.forEach(card => {
            const category = card.getAttribute('data-category');
            const title = card.querySelector('.document-title');
            const description = card.querySelector('.document-description');
            const downloadButton = card.querySelector('.btn-download');

            if (title && translations[lang].documentCategories[category]) {
                title.textContent = translations[lang].documentCategories[category];
            }
            if (description && translations[lang].documentDescriptions[category]) {
                description.textContent = translations[lang].documentDescriptions[category];
            }
            if (downloadButton) {
                downloadButton.textContent = translations[lang].downloadButton;
            }
        });

        // Update RTL layout for Arabic
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    }
}

// Initialize language from localStorage or default to English
document.addEventListener('DOMContentLoaded', () => {
    const savedLanguage = localStorage.getItem('language') || 'en';
    updateLanguage(savedLanguage);
});

// Language toggle button functionality
const languageToggle = document.getElementById('language-toggle');
if (languageToggle) {
    languageToggle.addEventListener('click', () => {
        const currentLang = document.documentElement.lang;
        const newLang = currentLang === 'en' ? 'ar' : 'en';
        document.documentElement.lang = newLang;
        localStorage.setItem('language', newLang);
        updateLanguage(newLang);
    });
} 