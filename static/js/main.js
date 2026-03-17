document.addEventListener('DOMContentLoaded', () => {
    // Force clear login fields to ensure placeholders are visible (prevents browser autofill)
    const loginUser = document.getElementById('login-username');
    const loginPass = document.getElementById('login-password');
    if (loginUser) loginUser.value = '';
    if (loginPass) loginPass.value = '';

    // Password Toggle Logic
    const passwordInput = document.getElementById('login-password');
    const passwordToggle = document.getElementById('password-toggle');
    const showIcon = document.querySelector('.toggle-icon-show');
    const hideIcon = document.querySelector('.toggle-icon-hide');

    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', () => {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

            // Toggle icons
            showIcon.style.display = isPassword ? 'none' : 'block';
            hideIcon.style.display = isPassword ? 'block' : 'none';
        });
    }

    // Registration Password Toggles
    document.querySelectorAll('.reg-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.parentElement.querySelector('input');
            const isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');

            toggle.querySelector('.toggle-icon-show').style.display = isPassword ? 'none' : 'block';
            toggle.querySelector('.toggle-icon-hide').style.display = isPassword ? 'block' : 'none';
        });
    });

    const modal = document.getElementById('authModal');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const closeBtn = document.querySelector('.modal-close');
    const overlay = document.querySelector('.modal-overlay');

    // Open Modal
    document.querySelectorAll('[data-modal]').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.getAttribute('data-modal');
            showForm(mode);
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        });
    });

    // Switch Forms
    document.querySelectorAll('[data-switch]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const mode = link.getAttribute('data-switch');
            showForm(mode);
        });
    });

    function showForm(mode) {
        if (mode === 'login') {
            loginForm.style.display = 'flex';
            registerForm.style.display = 'none';
            // Ensure login fields are empty so placeholders (shadow text) are visible
            if (loginUser) loginUser.value = '';
            if (loginPass) loginPass.value = '';
        } else {
            loginForm.style.display = 'none';
            registerForm.style.display = 'flex';
            // Also force clear registration fields
            document.querySelectorAll('#registerForm input').forEach(input => input.value = '');
        }
    }

    // Close Modal
    function closeModal() {
        modal.classList.remove('active');
        document.body.style.overflow = 'auto';
    }

    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

    // Escape Key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });

    // Real-time Password Match Validation
    const regPassword = document.getElementById('reg-password');
    const regConfirm = document.getElementById('reg-confirm');

    if (regPassword && regConfirm) {
        function validatePassword() {
            if (regPassword.value !== regConfirm.value) {
                regConfirm.setCustomValidity("Passwords Don't Match");
            } else {
                regConfirm.setCustomValidity('');
            }
        }
        regPassword.onchange = validatePassword;
        regConfirm.onkeyup = validatePassword;
    }

    // Real-time Username and Email Validation
    const regUsername = document.getElementById('reg-username');
    const usernameError = document.getElementById('username-error');
    const regEmail = document.getElementById('reg-email');
    const emailError = document.getElementById('email-error');
    const regSubmitBtn = document.querySelector('#registerForm button[type="submit"]');

    let isUsernameValid = false;
    let isEmailValid = false;

    function checkSubmitStatus() {
        if (regSubmitBtn) {
            regSubmitBtn.disabled = !(isUsernameValid && isEmailValid);
            regSubmitBtn.style.opacity = (isUsernameValid && isEmailValid) ? '1' : '0.5';
            regSubmitBtn.style.cursor = (isUsernameValid && isEmailValid) ? 'pointer' : 'not-allowed';
        }
    }

    if (regUsername && usernameError) {
        regUsername.addEventListener('blur', async () => {
            const username = regUsername.value.trim();
            if (username.length < 3) {
                isUsernameValid = false;
                checkSubmitStatus();
                return;
            }

            try {
                const response = await fetch('/api/check_username', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username })
                });
                const result = await response.json();

                if (!result.available) {
                    usernameError.textContent = result.message;
                    usernameError.style.display = 'block';
                    regUsername.style.borderColor = '#dc3545';
                    isUsernameValid = false;
                } else {
                    usernameError.style.display = 'none';
                    regUsername.style.borderColor = '#4CAF50';
                    isUsernameValid = true;
                }
                checkSubmitStatus();
            } catch (err) {
                console.error("Username validation error:", err);
            }
        });
    }

    if (regEmail && emailError) {
        regEmail.addEventListener('blur', async () => {
            const email = regEmail.value.trim();
            if (!email.includes('@')) {
                isEmailValid = false;
                checkSubmitStatus();
                return;
            }

            try {
                const response = await fetch('/api/check_email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                const result = await response.json();

                if (!result.available) {
                    emailError.textContent = result.message;
                    emailError.style.display = 'block';
                    regEmail.style.borderColor = '#dc3545';
                    isEmailValid = false;
                } else {
                    emailError.style.display = 'none';
                    regEmail.style.borderColor = '#4CAF50';
                    isEmailValid = true;
                }
                checkSubmitStatus();
            } catch (err) {
                console.error("Email validation error:", err);
            }
        });
    }

    // Auto-open modal ONLY if there are error alerts
    if (document.querySelector('.global-alerts .alert-error')) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Auto-hide alerts after 3 seconds
    const alerts = document.querySelectorAll('.global-alerts .alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translate(0, -10px)';
            alert.style.transition = 'all 0.4s ease-out';
            setTimeout(() => {
                alert.remove();
                // Ensure overflow is restored if no modals are open
                if (!document.querySelector('.modal.active')) {
                    document.body.style.overflow = 'auto';
                }
            }, 400);
        }, 2600);
    });

    // Sidebar Toggle Logic
    const sidebar = document.getElementById('categorySidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarClose = document.getElementById('sidebarClose');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebar && sidebarToggle && sidebarClose && sidebarOverlay) {
        function openSidebar() {
            sidebar.classList.add('open');
            sidebarOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }

        function closeSidebar() {
            sidebar.classList.remove('open');
            sidebarOverlay.classList.remove('active');
            document.body.style.overflow = 'auto';
        }

        sidebarToggle.addEventListener('click', openSidebar);
        sidebarClose.addEventListener('click', closeSidebar);
        sidebarOverlay.addEventListener('click', closeSidebar);

        // Escape Key to close sidebar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && sidebar.classList.contains('open')) {
                closeSidebar();
            }
        });

        // Close sidebar when clicking a link (optional, for smoother navigation)
        sidebar.querySelectorAll('.section-link').forEach(link => {
            link.addEventListener('click', closeSidebar);
        });

        // --- NEW: Mega Menu Tab Logic ---
        const megaTabs = document.querySelectorAll('.mega-tab');
        const tabContents = document.querySelectorAll('.mega-sections-content');

        megaTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const targetTab = tab.getAttribute('data-tab');

                // Update active tab button
                megaTabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');

                // Update visible content
                tabContents.forEach(content => {
                    content.style.display = 'none';
                    content.classList.remove('active-tab-content');
                });

                const activeContent = document.getElementById(`tab-${targetTab}`);
                if (activeContent) {
                    // For the main 'sections' tab, we use flex as defined in CSS
                    activeContent.style.display = targetTab === 'sections' ? 'flex' : 'block';
                    activeContent.classList.add('active-tab-content');
                }
            });
        });
    }

    // --- Global Theme/Mode Logic ---
    function applyTheme(theme) {
        const html = document.documentElement;
        const themeIcons = document.querySelectorAll('.mega-dropdown-toggle .icon');
        const themeRadios = document.getElementsByName('theme');
        const themeDarkCallback = document.getElementById('themeDark');
        const themeLightCallback = document.getElementById('themeLight');

        // Remove all specific theme attributes
        html.removeAttribute('data-theme');

        if (theme !== 'light') {
            html.setAttribute('data-theme', theme);
        }

        // Update icon in the menu
        themeIcons.forEach(icon => {
            if (theme === 'light') icon.textContent = '☀️';
            else if (theme === 'dark') icon.textContent = '🌙';
            else if (theme === 'read') icon.textContent = '👁️';
        });

        // Sync radio buttons if they exist
        if (themeDarkCallback && themeLightCallback) {
            if (theme === 'dark') {
                themeDarkCallback.checked = true;
            } else if (theme === 'light') {
                themeLightCallback.checked = true;
            }
        }

        localStorage.setItem('theme', theme);
    }

    // Handle all mega menu dropdowns (Theme/Mode & Account)
    const megaDropdowns = document.querySelectorAll('.mega-dropdown-container');

    megaDropdowns.forEach(container => {
        const toggle = container.querySelector('.mega-dropdown-toggle');

        if (toggle) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();

                // Close other dropdowns
                megaDropdowns.forEach(other => {
                    if (other !== container) other.classList.remove('active');
                });

                container.classList.toggle('active');
            });
        }
    });

    // Close dropdowns when clicking elsewhere
    document.addEventListener('click', (e) => {
        megaDropdowns.forEach(container => {
            if (!container.contains(e.target)) {
                container.classList.remove('active');
            }
        });
    });


    // Add listeners to mode options (globally)
    document.querySelectorAll('.mode-option').forEach(option => {
        option.addEventListener('click', () => {
            const theme = option.getAttribute('data-theme-value');
            applyTheme(theme);
        });
    });

    // Initial application
    const initialTheme = localStorage.getItem('theme') || 'light';
    applyTheme(initialTheme);

    // New Navigation Menu Logic
    const navToggle = document.getElementById('navToggle');
    const navBar = document.getElementById('navBar');
    const dropdowns = document.querySelectorAll('.nav-dropdown');

    if (navToggle && navBar) {
        navToggle.addEventListener('click', () => {
            navToggle.classList.toggle('active');
            navBar.classList.toggle('active');
            document.body.style.overflow = navBar.classList.contains('active') ? 'hidden' : 'auto';
        });

        // Handle mobile dropdowns
        dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            if (toggle) {
                toggle.addEventListener('click', (e) => {
                    if (window.innerWidth <= 868) {
                        e.preventDefault();
                        dropdown.classList.toggle('active');
                    }
                });
            }
        });

        // Close menu when clicking links (mobile)
        navBar.querySelectorAll('.nav-link:not(.dropdown-toggle)').forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                navBar.classList.remove('active');
                document.body.style.overflow = 'auto';
            });
        });
    }

    // 3. Handle Dark Mode Toggle (Radio Buttons)
    const themeRadios = document.getElementsByName('theme');

    themeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            applyTheme(e.target.value);
        });
    });

    // 4. Handle Brightness Slider & Eye Comfort Shield
    const eyeComfortToggle = document.getElementById('eyeComfortToggle');
    const eyeComfortSlider = document.getElementById('eyeComfortSlider');
    const eyeComfortIntensityControl = document.getElementById('eyeComfortIntensityControl');
    const savedEyeComfort = localStorage.getItem('eyeComfort');
    const savedEyeComfortIntensity = localStorage.getItem('eyeComfortIntensity');
    // savedBrightness already declared above

    // Helper to apply all filters
    function applyFilters() {
        // Use the saved values or defaults
        const brightness = localStorage.getItem('brightness') || 100;
        const eyeComfort = localStorage.getItem('eyeComfort') === 'true';
        const eyeComfortIntensity = localStorage.getItem('eyeComfortIntensity') || 30; // Default intensity

        let filterString = `brightness(${brightness}%)`;
        if (eyeComfort) {
            // Basic sepia for warmth, intensity adjustable
            filterString += ` sepia(${eyeComfortIntensity}%)`;
        }

        htmlElement.style.filter = filterString;
    }

    // Initialize Eye Comfort
    if (savedEyeComfort === 'true') {
        if (eyeComfortToggle) eyeComfortToggle.checked = true;
        if (eyeComfortIntensityControl) eyeComfortIntensityControl.style.display = 'flex';
        applyFilters();
    }

    // Initialize Brightness if it exists
    if (savedBrightness) {
        if (brightnessSlider) brightnessSlider.value = savedBrightness;
        applyFilters();
    }

    if (savedEyeComfortIntensity && eyeComfortSlider) {
        eyeComfortSlider.value = savedEyeComfortIntensity;
    }

    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', () => {
            localStorage.setItem('brightness', brightnessSlider.value);
            applyFilters();
        });
    }

    if (eyeComfortToggle) {
        eyeComfortToggle.addEventListener('change', () => {
            const isChecked = eyeComfortToggle.checked;
            localStorage.setItem('eyeComfort', isChecked);

            if (eyeComfortIntensityControl) {
                eyeComfortIntensityControl.style.display = isChecked ? 'flex' : 'none';
            }

            applyFilters();
        });
    }

    if (eyeComfortSlider) {
        eyeComfortSlider.addEventListener('input', () => {
            localStorage.setItem('eyeComfortIntensity', eyeComfortSlider.value);
            applyFilters();
        });
    }

    /* -------------------------------------------------------------
       Voice Assistant Logic
    ------------------------------------------------------------- */
    function initVoiceAssistant() {
        // We need to fetch user settings. Since we don't have a direct API, 
        // we can look for the settings in the DOM if we are on the profile page,
        // OR we can rely on a global JS variable injected by the template.
        // BUT, the requirement is to read news automatically.
        // For this to work, the user needs to have the page open.

        // Let's assume the backend injects user_data into a global var if logged in.
        // If not, we can't really check.
        // Alternatively, we can make a lightweight fetch to an API endpoint every minute.

        // Since we didn't build a clear API, let's try to find the settings from the DOM 
        // if we are on the profile page, and save them to localStorage for persistence across pages.
        // This is a robust way to handle it without new API endpoints.

        const voiceTimeInput = document.querySelector('input[name="voice_time"]');
        const voiceEnabledInput = document.getElementById('voice_enabled');

        if (voiceTimeInput && voiceEnabledInput) {
            // We are on profile page (or edit mode), save to local storage on save
            // Actually, the form submit handles saving to DB.
            // On page load, we should sync localStorage with DB values if present.
            const currentVoiceTime = voiceTimeInput.value;
            const currentVoiceEnabled = voiceEnabledInput.checked;

            if (currentVoiceTime) localStorage.setItem('aura_voice_time', currentVoiceTime);
            localStorage.setItem('aura_voice_enabled', currentVoiceEnabled);
        }

        // Check every minute
        setInterval(checkAlarm, 60000);

        // Also check on load
        checkAlarm();
    }

    let hasPlayedToday = false;

    function checkAlarm() {
        const enabled = localStorage.getItem('aura_voice_enabled') === 'true';
        const time = localStorage.getItem('aura_voice_time');

        if (!enabled || !time) return;

        const now = new Date();
        const currentHours = String(now.getHours()).padStart(2, '0');
        const currentMinutes = String(now.getMinutes()).padStart(2, '0');
        const currentTime = `${currentHours}:${currentMinutes}`;

        // Simple check to prevent multiple plays in the same minute
        // In a real app we'd track the date.
        const lastPlayedDate = localStorage.getItem('aura_last_played_date');
        const todayDate = now.toDateString();

        if (currentTime === time && lastPlayedDate !== todayDate) {
            playDailyBriefing();
            localStorage.setItem('aura_last_played_date', todayDate);
        }
    }

    function playDailyBriefing() {
        // Collect news. Since we might not be on the home page, we might not have the news logic.
        // But the requirements say "all the news should be available... read out loud".
        // Use a hidden container or fetch the home page content if needed.
        // Easiest is to redirect to home or assume user is on a news page.
        // Let's assume user is on the site. If on home, we read featured + latest.
        // If not on home, we can try to fetch the home html or just say "Please go to home".
        // BETTER: Fetch the index page HTML, parse it, and read.

        // However, for simplicity and reliability in this specific task context:
        // We will read what is currently on the screen if possible,
        // OR we can make a fetch request to the root '/' which returns the rendered index.

        // Let's try to read the "Featured" article from the DOM if it exists.

        const featuredTitle = document.querySelector('.featured-title');
        const latestTitles = document.querySelectorAll('.news-card h3');

        if (!featuredTitle && latestTitles.length === 0) {
            // Not on home page, maybe redirect or fetch?
            // Let's try to speak a generic message or return.
            console.log("No news found on current page to read.");
            return;
        }

        const lang = document.documentElement.lang || 'en'; // Assuming we set <html lang="en/ml">
        // If not set, check session logic... but we are in JS.
        // We can check a visible element text to guess language.

        // Construct the text
        let speechText = "";

        if (lang === 'ml') {
            speechText += "നമസ്കാരം, ഇന്നത്തെ പ്രധാന വാർത്തകൾ. ";
        } else {
            speechText += "Good morning. Here is your daily briefing. ";
        }

        if (featuredTitle) {
            speechText += featuredTitle.innerText + ". ";
            const featuredExcerpt = document.querySelector('.featured-excerpt');
            if (featuredExcerpt) speechText += featuredExcerpt.innerText + ". ";
        }

        if (latestTitles.length > 0) {
            if (lang === 'ml') speechText += "മറ്റ് പ്രധാന വാർത്തകൾ: ";
            else speechText += "In other news: ";

            latestTitles.forEach((title, index) => {
                if (index < 3) { // Top 3
                    speechText += title.innerText + ". ";
                }
            });
        }

        speak(speechText, lang);
    }

    function speak(text, lang) {
        window.speechSynthesis.cancel(); // Stop any current speech

        const utterance = new SpeechSynthesisUtterance(text);

        // Language selection
        if (lang === 'ml' || text.match(/[\u0D00-\u0D7F]/)) {
            utterance.lang = 'ml-IN';
        } else {
            utterance.lang = 'en-US';
        }

        // Voice selection (optional refinement)
        const voices = window.speechSynthesis.getVoices();
        if (lang === 'ml') {
            const malVoice = voices.find(v => v.lang.includes('ml'));
            if (malVoice) utterance.voice = malVoice;
        }

        window.speechSynthesis.speak(utterance);
    }

    // Trigger initialization
    initVoiceAssistant();

    // -------------------------------------------------------------
    // Voice Assistant Logic (Audio News Briefing)
    // -------------------------------------------------------------
    function checkScheduledBriefing() {
        // Ensure variables from base.html are available
        if (typeof userVoiceEnabled === 'undefined' || !userVoiceEnabled || !userVoiceTime || typeof newsData === 'undefined') return;

        const now = new Date();
        const currentHours = now.getHours().toString().padStart(2, '0');
        const currentMinutes = now.getMinutes().toString().padStart(2, '0');
        const currentTime = `${currentHours}:${currentMinutes}`;

        console.log(`[Voice Check] Current: ${currentTime} | Scheduled: ${userVoiceTime} | Enabled: ${userVoiceEnabled} | Triggered: ${sessionStorage.getItem(`voice_triggered_${currentTime}`)}`);

        // Check if current time matches scheduled time
        // We use a flag in sessionStorage to prevent multiple triggers in the same minute
        const hasTriggered = sessionStorage.getItem(`voice_triggered_${currentTime}`);

        if (currentTime === userVoiceTime && !hasTriggered) {
            sessionStorage.setItem(`voice_triggered_${currentTime}`, 'true');
            readNewsBriefing();
        }
    }

    function readNewsBriefing() {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel(); // Clear any existing queue

            // Intro
            const introText = (typeof currentLang !== 'undefined' && currentLang === 'ml')
                ? "നമസ്കാരം, ഇന്നത്തെ പ്രധാന വാർത്തകൾ." // Malayalam Intro
                : "Here is your daily news briefing from JANAVAAKYA – Voice of the People.";

            const intro = new SpeechSynthesisUtterance(introText);
            intro.lang = (typeof currentLang !== 'undefined' && currentLang === 'ml') ? 'ml-IN' : 'en-US';
            window.speechSynthesis.speak(intro);

            // Read each article
            if (typeof newsData !== 'undefined' && Array.isArray(newsData)) {
                newsData.forEach((article, index) => {
                    // Determine content based on language
                    const title = (typeof currentLang !== 'undefined' && currentLang === 'ml') ? (article.title_ml || article.title) : article.title;
                    const content = (typeof currentLang !== 'undefined' && currentLang === 'ml') ? (article.content_ml || article.content) : article.content;

                    const textToRead = `${title}. ${content}`;
                    const utterance = new SpeechSynthesisUtterance(textToRead);
                    utterance.lang = (typeof currentLang !== 'undefined' && currentLang === 'ml') ? 'ml-IN' : 'en-US';

                    // Add a small pause between articles
                    const pause = new SpeechSynthesisUtterance('');
                    pause.pause = 1000; // 1 second pause (approx)

                    window.speechSynthesis.speak(utterance);
                    window.speechSynthesis.speak(pause);
                });
            }
        }
    }

    // --- Multi-modal Search Logic ---
    const voiceSearchBtn = document.getElementById('voiceSearchBtn');
    const imageSearchBtn = document.getElementById('imageSearchBtn');
    const imageSearchInput = document.getElementById('imageSearchInput');
    const imageSearchForm = document.getElementById('imageSearchForm');
    const homeSearchInput = document.getElementById('homeSearchInput');
    const homeSearchForm = document.getElementById('homeSearchForm');

    // 1. Image Search (Triggers file upload)
    if (imageSearchBtn && imageSearchInput && imageSearchForm) {
        imageSearchBtn.addEventListener('click', () => {
            imageSearchInput.click();
        });

        imageSearchInput.addEventListener('change', () => {
            if (imageSearchInput.files && imageSearchInput.files.length > 0) {
                // Visual feedback
                imageSearchBtn.style.color = 'var(--primary)';
                if (homeSearchInput) homeSearchInput.placeholder = "Uploading image for analysis...";
                // Auto-submit the hidden form
                imageSearchForm.submit();
            }
        });
    }

    // 2. Voice Search (Web Speech API)
    if (voiceSearchBtn && homeSearchInput && homeSearchForm) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false;
            // Use current session language if available
            recognition.lang = (typeof currentLang !== 'undefined' && currentLang === 'ml') ? 'ml-IN' : 'en-US';
            recognition.interimResults = false;
            recognition.maxAlternatives = 1;

            let isRecording = false;

            voiceSearchBtn.addEventListener('click', () => {
                if (isRecording) {
                    recognition.stop();
                    return;
                }

                try {
                    // Try to stop synthesis if it's talking
                    if ('speechSynthesis' in window) { window.speechSynthesis.cancel(); }

                    recognition.start();
                    isRecording = true;
                    voiceSearchBtn.classList.add('listening');
                    homeSearchInput.placeholder = "Listening... Speak now";
                } catch (e) {
                    console.error("Speech recognition error:", e);
                }
            });

            recognition.onresult = (event) => {
                const speechResult = event.results[0][0].transcript;
                homeSearchInput.value = speechResult;
                voiceSearchBtn.classList.remove('listening');
                isRecording = false;

                // Automatically submit the form
                setTimeout(() => {
                    homeSearchForm.submit();
                }, 500);
            };

            recognition.onspeechend = () => {
                recognition.stop();
            };

            recognition.onerror = (event) => {
                console.error("Speech recognition error:", event.error);
                voiceSearchBtn.classList.remove('listening');
                homeSearchInput.placeholder = "Speech not recognized. Try again.";
                isRecording = false;
                setTimeout(() => {
                    homeSearchInput.placeholder = "Search news, topics, or paste image...";
                }, 3000);
            };

            recognition.onend = () => {
                voiceSearchBtn.classList.remove('listening');
                isRecording = false;
                if (!homeSearchInput.value) {
                    homeSearchInput.placeholder = "Search news, topics, or paste image...";
                }
            };
        } else {
            // Browser doesn't support speech recognition
            voiceSearchBtn.addEventListener('click', () => {
                alert("Sorry, your browser doesn't support voice search. Try Chrome or Edge.");
            });
            voiceSearchBtn.style.opacity = '0.5';
            voiceSearchBtn.style.cursor = 'not-allowed';
        }
    }

    // Check every 30 seconds
    setInterval(checkScheduledBriefing, 30000);
    // Initial check
    setTimeout(checkScheduledBriefing, 2000);

});
