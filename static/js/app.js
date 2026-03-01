// ── Voice Browser Modal ──────────────────────────────────────

class VoiceBrowser {
    constructor(options = {}) {
        this.voices = [];
        this.categories = [];
        this.selectedVoice = null;
        this.activeCategory = 'all';
        this.activeGender = 'all';
        this.searchQuery = '';
        this.isOpen = false;
        this.onChange = options.onChange || (() => {});

        // Audio preview
        this.previewAudio = new Audio();
        this.previewingVoice = null;

        this.els = {
            trigger: document.getElementById('voice-trigger'),
            triggerText: document.getElementById('voice-trigger-text'),
            modal: document.getElementById('voice-modal'),
            close: document.getElementById('voice-modal-close'),
            search: document.getElementById('voice-search'),
            genderFilters: document.getElementById('voice-gender-filters'),
            categoryFilters: document.getElementById('voice-category-filters'),
            cardGrid: document.getElementById('voice-card-grid'),
            count: document.getElementById('voice-modal-count'),
        };

        this._setupEvents();
    }

    _setupEvents() {
        // Open modal
        this.els.trigger.addEventListener('click', () => this.open());

        // Close modal
        this.els.close.addEventListener('click', () => this.close());
        this.els.modal.addEventListener('click', (e) => {
            if (e.target === this.els.modal) this.close();
        });

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) this.close();
        });

        // Search
        this.els.search.addEventListener('input', () => {
            this.searchQuery = this.els.search.value.toLowerCase().trim();
            this._renderCards();
        });

        // Gender filters
        this.els.genderFilters.querySelectorAll('.filter-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                this.els.genderFilters.querySelectorAll('.filter-chip')
                    .forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.activeGender = chip.dataset.gender;
                this._renderCards();
            });
        });

        // Preview audio ended
        this.previewAudio.addEventListener('ended', () => {
            this._clearPreviewState();
        });
    }

    setVoices(voices, categories) {
        this.voices = voices;
        this.categories = categories;

        // Render category chips in modal
        const container = this.els.categoryFilters;
        // Remove old dynamic chips (keep the "All" button)
        container.querySelectorAll('.category-chip:not([data-category="all"])').forEach(c => c.remove());

        categories.forEach(cat => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'category-chip';
            btn.dataset.category = cat.id;
            btn.textContent = cat.label;
            btn.title = cat.description;
            container.appendChild(btn);
        });

        // Bind category click handlers (including "All")
        container.querySelectorAll('.category-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                container.querySelectorAll('.category-chip')
                    .forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.activeCategory = chip.dataset.category;
                this._renderCards();
            });
        });

        // Select default voice if none selected
        if (!this.selectedVoice && voices.length > 0) {
            this.selectedVoice = voices[0].api_name;
        }

        this._updateTrigger();
        this._renderCards();
    }

    selectVoice(apiName) {
        const voice = this.voices.find(v => v.api_name === apiName);
        if (voice) {
            this.selectedVoice = apiName;
            this._updateTrigger();
            this._renderCards();
        }
    }

    getSelectedVoice() {
        return this.selectedVoice || '';
    }

    open() {
        this.isOpen = true;
        this.els.modal.hidden = false;
        this.els.search.value = '';
        this.searchQuery = '';
        this._renderCards();
        // Focus search after opening
        setTimeout(() => this.els.search.focus(), 50);
    }

    close() {
        this.isOpen = false;
        this.els.modal.hidden = true;
        this._stopPreview();
    }

    // ── Private methods ──

    _filterVoices() {
        return this.voices.filter(v => {
            // Category filter
            if (this.activeCategory !== 'all' && v.category !== this.activeCategory) return false;
            // Gender filter
            if (this.activeGender !== 'all' && v.gender !== this.activeGender) return false;
            // Search filter
            if (this.searchQuery) {
                const haystack = (v.display_name + ' ' + v.category).toLowerCase();
                if (!haystack.includes(this.searchQuery)) return false;
            }
            return true;
        });
    }

    _renderCards() {
        const grid = this.els.cardGrid;
        grid.innerHTML = '';

        const filtered = this._filterVoices();

        filtered.forEach(voice => {
            const card = document.createElement('div');
            card.className = 'voice-card' + (voice.api_name === this.selectedVoice ? ' selected' : '');
            card.dataset.voice = voice.api_name;

            const catDef = this.categories.find(c => c.id === voice.category);
            const catLabel = catDef ? catDef.label : voice.category;

            card.innerHTML =
                '<div class="voice-card-name">' + this._esc(voice.display_name) + '</div>' +
                '<div class="voice-card-meta">' +
                    '<span class="voice-badge voice-badge-' + voice.gender + '">' + voice.gender + '</span>' +
                    '<span>' + this._esc(catLabel) + '</span>' +
                '</div>' +
                '<div class="voice-card-actions">' +
                    '<button type="button" class="voice-preview-btn" data-voice="' +
                        voice.api_name + '" title="Preview this voice">&#9654; Preview</button>' +
                '</div>';

            // Click card to select
            card.addEventListener('click', (e) => {
                // Don't select when clicking preview button
                if (e.target.closest('.voice-preview-btn')) return;
                this._selectAndClose(voice.api_name);
            });

            // Preview button
            const previewBtn = card.querySelector('.voice-preview-btn');
            previewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this._togglePreview(voice.api_name, previewBtn);
            });

            grid.appendChild(card);
        });

        // Update count
        this.els.count.textContent = filtered.length + ' voice' + (filtered.length !== 1 ? 's' : '');
    }

    _selectAndClose(apiName) {
        this.selectedVoice = apiName;
        this._updateTrigger();
        this.close();
        this.onChange(apiName);
    }

    _updateTrigger() {
        const voice = this.voices.find(v => v.api_name === this.selectedVoice);
        if (voice) {
            const catDef = this.categories.find(c => c.id === voice.category);
            const catLabel = catDef ? catDef.label : voice.category;
            this.els.triggerText.textContent =
                '\uD83C\uDF99\uFE0F ' + voice.display_name + ' (' + catLabel + ', ' + voice.gender + ')';
        } else {
            this.els.triggerText.textContent = 'Select a voice...';
        }
    }

    _togglePreview(voiceName, btn) {
        // If same voice is playing, stop it
        if (this.previewingVoice === voiceName && !this.previewAudio.paused) {
            this._stopPreview();
            return;
        }

        // Stop any current preview
        this._stopPreview();

        // Start new preview
        btn.classList.add('playing');
        btn.innerHTML = '&#9646;&#9646; Stop';
        this.previewingVoice = voiceName;
        this.previewAudio.src = '/static/samples/' + voiceName + '.wav';
        this.previewAudio.play().catch(() => {
            // Sample file might not exist yet
            btn.classList.remove('playing');
            btn.innerHTML = '&#9654; Preview';
            this.previewingVoice = null;
        });
    }

    _stopPreview() {
        this.previewAudio.pause();
        this.previewAudio.currentTime = 0;
        this._clearPreviewState();
    }

    _clearPreviewState() {
        this.previewingVoice = null;
        this.els.cardGrid.querySelectorAll('.voice-preview-btn.playing').forEach(btn => {
            btn.classList.remove('playing');
            btn.innerHTML = '&#9654; Preview';
        });
    }

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}


// ── Main App ─────────────────────────────────────────────────

class StorytellerApp {
    constructor() {
        this.jobId = null;
        this.pollInterval = null;
        this.startTime = null;
        this.totalChunks = 0;
        this.selectedFile = null;
        this.activeTab = 'upload';

        // Voice data (populated by loadVoices)
        this.voiceData = [];
        this.categories = [];
        this.defaultVoice = '';
        this.userTier = 'free';

        // Presets & source texts
        this.presets = [];
        this.sourceTexts = [];
        this.loadedSourceTextId = null;
        this.moods = [];
        this.customMoodAllowed = false;
        this.selectedMood = '';

        this.els = {
            tabs: document.querySelectorAll('.tab'),
            tabUpload: document.getElementById('tab-upload'),
            tabPaste: document.getElementById('tab-paste'),
            dropZone: document.getElementById('drop-zone'),
            fileInput: document.getElementById('file-input'),
            fileSelected: document.getElementById('file-selected'),
            fileName: document.getElementById('file-name'),
            clearFile: document.getElementById('clear-file'),
            textInput: document.getElementById('text-input'),
            speedSlider: document.getElementById('speed-slider'),
            speedValue: document.getElementById('speed-value'),
            pitchSlider: document.getElementById('pitch-slider'),
            pitchValue: document.getElementById('pitch-value'),
            btnGenerate: document.getElementById('btn-generate'),
            errorBanner: document.getElementById('error-banner'),
            errorMessage: document.getElementById('error-message'),
            clearError: document.getElementById('clear-error'),
            progressSection: document.getElementById('progress-section'),
            progressBar: document.getElementById('progress-bar'),
            progressChunks: document.getElementById('progress-chunks'),
            progressTime: document.getElementById('progress-time'),
            resultSection: document.getElementById('result-section'),
            audioPlayer: document.getElementById('audio-player'),
            presetSelect: document.getElementById('preset-select'),
            btnSavePreset: document.getElementById('btn-save-preset'),
            btnDeletePreset: document.getElementById('btn-delete-preset'),
            audioTitle: document.getElementById('audio-title'),
            saveTextCheck: document.getElementById('save-text-check'),
            saveTextTitle: document.getElementById('save-text-title'),
            sourceTextPicker: document.getElementById('source-text-picker'),
            sourceTextSelect: document.getElementById('source-text-select'),
            tierUpgradeNote: document.getElementById('tier-upgrade-note'),
            tierUpgradeBanner: document.getElementById('tier-upgrade-banner'),
            moodSection: document.getElementById('mood-section'),
            moodChips: document.getElementById('mood-chips'),
            customMoodField: document.getElementById('custom-mood-field'),
            customMoodInput: document.getElementById('custom-mood-input'),
        };

        // Voice browser modal
        this.voiceBrowser = new VoiceBrowser({
            onChange: (apiName) => this.onVoiceChanged(apiName),
        });

        this.setupEventListeners();
        this.loadVoices();
        this.loadPresets();
        this.loadSourceTexts();
        this.checkUrlParams();
    }

    onVoiceChanged(apiName) {
        this.els.presetSelect.value = '';
        this.els.btnDeletePreset.hidden = true;
        this.updateMoodVisibility();
    }

    setupEventListeners() {
        // Tab switching
        this.els.tabs.forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Drop zone
        const dz = this.els.dropZone;
        dz.addEventListener('click', () => this.els.fileInput.click());
        dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
        dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
        dz.addEventListener('drop', e => {
            e.preventDefault();
            dz.classList.remove('drag-over');
            if (e.dataTransfer.files.length) this.setFile(e.dataTransfer.files[0]);
        });

        this.els.fileInput.addEventListener('change', () => {
            if (this.els.fileInput.files.length) this.setFile(this.els.fileInput.files[0]);
        });

        this.els.clearFile.addEventListener('click', e => {
            e.stopPropagation();
            this.clearFile();
        });

        // Sliders
        this.els.speedSlider.addEventListener('input', () => {
            this.els.speedValue.textContent = this.els.speedSlider.value + 'x';
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        });
        this.els.pitchSlider.addEventListener('input', () => {
            this.els.pitchValue.textContent = this.els.pitchSlider.value;
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        });

        // Generate
        this.els.btnGenerate.addEventListener('click', () => this.submit());

        // Clear error
        this.els.clearError.addEventListener('click', () => this.hideError());

        // Presets
        this.els.presetSelect.addEventListener('change', () => this.applyPreset());
        this.els.btnSavePreset.addEventListener('click', () => this.savePreset());
        this.els.btnDeletePreset.addEventListener('click', () => this.deletePreset());

        // Save text checkbox
        this.els.saveTextCheck.addEventListener('change', () => {
            this.els.saveTextTitle.hidden = !this.els.saveTextCheck.checked;
        });

        // Source text picker
        this.els.sourceTextSelect.addEventListener('change', () => this.loadSourceText());
    }

    // ── Voice loading ────────────────────────────────────────────

    async loadVoices() {
        try {
            const resp = await fetch('/api/voices');
            const data = await resp.json();
            this.voiceData = data.voices;
            this.categories = data.categories;
            this.defaultVoice = data.default;
            this.userTier = data.tier || 'free';
            this.moods = data.moods || [];
            this.customMoodAllowed = data.custom_mood_allowed || false;

            // Pass data to voice browser
            this.voiceBrowser.setVoices(this.voiceData, this.categories);
            if (this.defaultVoice) {
                this.voiceBrowser.selectVoice(this.defaultVoice);
            }

            this.renderMoodChips();
            if (this.userTier === 'free') {
                this.renderUpgradePrompts();
            }
        } catch (err) {
            console.error('Failed to load voices:', err);
        }
    }

    renderUpgradePrompts() {
        const linkUrl = '/api/patreon/link';
        // Note inside voice settings
        if (this.els.tierUpgradeNote) {
            this.els.tierUpgradeNote.innerHTML =
                '<p class="tier-upgrade-note">You\'re using the free voice. ' +
                '<a href="' + linkUrl + '">Connect your Patreon</a> to unlock all 99 premium voices.</p>';
        }
        // Banner above generate button
        if (this.els.tierUpgradeBanner) {
            this.els.tierUpgradeBanner.innerHTML =
                '<div class="tier-upgrade-banner">' +
                '<span>Want more voices? </span>' +
                '<a href="' + linkUrl + '" class="landing-btn landing-btn-primary" ' +
                'style="padding:0.5rem 1.2rem;font-size:0.9rem;">Connect Patreon to Unlock All Voices</a>' +
                '</div>';
        }
    }

    // ── Moods (Gemini voices only) ───────────────────────────────

    renderMoodChips() {
        const container = this.els.moodChips;
        if (!container) return;
        container.innerHTML = '';

        if (this.moods.length === 0 && !this.customMoodAllowed) {
            if (this.els.moodSection) this.els.moodSection.hidden = true;
            return;
        }

        // "None" chip (default)
        const noneChip = document.createElement('button');
        noneChip.type = 'button';
        noneChip.className = 'mood-chip active';
        noneChip.dataset.mood = '';
        noneChip.textContent = 'None';
        noneChip.title = 'No mood \u2014 default Gemini delivery';
        container.appendChild(noneChip);

        // Mood preset chips
        this.moods.forEach(mood => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'mood-chip';
            chip.dataset.mood = mood.id;
            chip.textContent = mood.icon + ' ' + mood.label;
            chip.title = mood.description;
            container.appendChild(chip);
        });

        // Click handlers
        container.querySelectorAll('.mood-chip').forEach(chip => {
            chip.addEventListener('click', () => {
                container.querySelectorAll('.mood-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
                this.selectedMood = chip.dataset.mood;
            });
        });

        // Custom mood field
        if (this.customMoodAllowed && this.els.customMoodField) {
            this.els.customMoodField.hidden = false;
        }

        this.updateMoodVisibility();
    }

    updateMoodVisibility() {
        const section = this.els.moodSection;
        if (!section) return;

        const voiceName = this.voiceBrowser.getSelectedVoice();
        const voice = this.voiceData.find(v => v.api_name === voiceName);
        const isGemini = voice && voice.category === 'gemini';
        const hasMoods = this.moods.length > 0 || this.customMoodAllowed;
        section.hidden = !isGemini || !hasMoods;
    }

    setMoodById(moodId) {
        this.selectedMood = moodId || '';
        if (!this.els.moodChips) return;
        this.els.moodChips.querySelectorAll('.mood-chip').forEach(c => {
            c.classList.toggle('active', c.dataset.mood === this.selectedMood);
        });
    }

    // ── Presets ──────────────────────────────────────────────────

    async loadPresets() {
        try {
            const resp = await fetch('/api/presets');
            const data = await resp.json();
            this.presets = data.presets || [];
            this.renderPresetOptions();
        } catch (err) {
            console.error('Failed to load presets:', err);
        }
    }

    renderPresetOptions() {
        const select = this.els.presetSelect;
        select.innerHTML = '<option value="">Custom settings</option>';
        this.presets.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            select.appendChild(opt);
        });
    }

    applyPreset() {
        const presetId = this.els.presetSelect.value;
        if (!presetId) {
            this.els.btnDeletePreset.hidden = true;
            return;
        }

        const preset = this.presets.find(p => p.id === presetId);
        if (!preset) return;

        // Apply voice via browser
        this.voiceBrowser.selectVoice(preset.voice_name);

        // Apply speed & pitch
        this.els.speedSlider.value = preset.speaking_rate;
        this.els.speedValue.textContent = preset.speaking_rate + 'x';
        this.els.pitchSlider.value = preset.pitch;
        this.els.pitchValue.textContent = preset.pitch;

        // Apply mood
        this.updateMoodVisibility();
        this.setMoodById(preset.mood_id || '');

        this.els.btnDeletePreset.hidden = false;
    }

    async savePreset() {
        const name = prompt('Preset name:');
        if (!name || !name.trim()) return;

        try {
            const resp = await fetch('/api/presets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: name.trim(),
                    voice_name: this.voiceBrowser.getSelectedVoice(),
                    speaking_rate: parseFloat(this.els.speedSlider.value),
                    pitch: parseFloat(this.els.pitchSlider.value),
                    mood_id: this.selectedMood || '',
                }),
            });
            const data = await resp.json();

            if (data.error) {
                this.showError(data.error);
                return;
            }

            this.presets.push(data.preset);
            this.renderPresetOptions();
            this.els.presetSelect.value = data.preset.id;
            this.els.btnDeletePreset.hidden = false;
        } catch (err) {
            this.showError('Failed to save preset');
        }
    }

    async deletePreset() {
        const presetId = this.els.presetSelect.value;
        if (!presetId) return;
        if (!confirm('Delete this preset?')) return;

        try {
            await fetch('/api/presets/' + presetId, {method: 'DELETE'});
            this.presets = this.presets.filter(p => p.id !== presetId);
            this.renderPresetOptions();
            this.els.presetSelect.value = '';
            this.els.btnDeletePreset.hidden = true;
        } catch (err) {
            this.showError('Failed to delete preset');
        }
    }

    // ── Source Texts ─────────────────────────────────────────────

    async loadSourceTexts() {
        try {
            const resp = await fetch('/api/texts');
            const data = await resp.json();
            this.sourceTexts = data.texts || [];
            this.renderSourceTextOptions();
        } catch (err) {
            console.error('Failed to load source texts:', err);
        }
    }

    renderSourceTextOptions() {
        const select = this.els.sourceTextSelect;
        select.innerHTML = '<option value="">-- Load from My Texts --</option>';

        if (this.sourceTexts.length === 0) {
            this.els.sourceTextPicker.hidden = true;
            return;
        }

        this.els.sourceTextPicker.hidden = false;
        this.sourceTexts.forEach(t => {
            const opt = document.createElement('option');
            opt.value = t.id;
            opt.textContent = t.title + ' (' + t.char_count.toLocaleString() + ' chars)';
            select.appendChild(opt);
        });
    }

    async loadSourceText() {
        const textId = this.els.sourceTextSelect.value;
        if (!textId) {
            this.loadedSourceTextId = null;
            return;
        }

        try {
            const resp = await fetch('/api/texts/' + textId);
            const data = await resp.json();
            if (data.text) {
                this.els.textInput.value = data.text.content;
                this.loadedSourceTextId = textId;
                // Switch to paste tab
                this.switchTab('paste');
                // Pre-fill audio title from text title
                if (!this.els.audioTitle.value) {
                    this.els.audioTitle.value = data.text.title;
                }
            }
        } catch (err) {
            this.showError('Failed to load text');
        }
    }

    checkUrlParams() {
        const params = new URLSearchParams(window.location.search);
        const loadTextId = params.get('load_text');
        if (loadTextId) {
            // Will be loaded once source texts are fetched
            this.pendingLoadTextId = loadTextId;
            const origRender = this.renderSourceTextOptions.bind(this);
            this.renderSourceTextOptions = () => {
                origRender();
                if (this.pendingLoadTextId) {
                    this.els.sourceTextSelect.value = this.pendingLoadTextId;
                    this.loadSourceText();
                    this.pendingLoadTextId = null;
                    this.renderSourceTextOptions = origRender;
                }
            };
        }
    }

    // ── Core app logic ──────────────────────────────────────────

    switchTab(tab) {
        this.activeTab = tab;
        this.els.tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === tab));
        this.els.tabUpload.classList.toggle('active', tab === 'upload');
        this.els.tabPaste.classList.toggle('active', tab === 'paste');
    }

    setFile(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!['md', 'txt', 'markdown'].includes(ext)) {
            this.showError('Please select a .md, .txt, or .markdown file');
            return;
        }
        this.selectedFile = file;
        this.els.fileName.textContent = file.name + ' (' + this.formatSize(file.size) + ')';
        this.els.fileSelected.hidden = false;
        // Use filename (without extension) as default audio title
        if (!this.els.audioTitle.value) {
            this.els.audioTitle.value = file.name.replace(/\.[^.]+$/, '');
        }
    }

    clearFile() {
        this.selectedFile = null;
        this.els.fileInput.value = '';
        this.els.fileSelected.hidden = true;
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    showError(msg) {
        this.els.errorMessage.textContent = msg;
        this.els.errorBanner.hidden = false;
    }

    hideError() {
        this.els.errorBanner.hidden = true;
    }

    async submit() {
        this.hideError();
        this.els.resultSection.hidden = true;
        this.els.progressSection.hidden = true;
        this.els.audioPlayer.pause();
        this.els.audioPlayer.removeAttribute('src');
        this.els.audioPlayer.load();

        const formData = new FormData();

        if (this.activeTab === 'upload') {
            if (!this.selectedFile) {
                this.showError('Please select a file to upload');
                return;
            }
            formData.append('file', this.selectedFile);
        } else {
            const text = this.els.textInput.value.trim();
            if (!text) {
                this.showError('Please enter some text');
                return;
            }
            formData.append('text', text);
        }

        formData.append('voice_name', this.voiceBrowser.getSelectedVoice());
        formData.append('speaking_rate', this.els.speedSlider.value);
        formData.append('pitch', this.els.pitchSlider.value);

        // Mood (Gemini voices only)
        if (this.selectedMood) {
            formData.append('mood_id', this.selectedMood);
        }
        const customMoodText = this.els.customMoodInput ? this.els.customMoodInput.value.trim() : '';
        if (customMoodText && this.customMoodAllowed) {
            formData.append('custom_mood', customMoodText);
        }

        // Audio title
        const audioTitle = this.els.audioTitle.value.trim() || 'Untitled';
        formData.append('audio_title', audioTitle);

        // Save text option
        if (this.els.saveTextCheck.checked) {
            formData.append('save_text', '1');
            formData.append('text_title', this.els.saveTextTitle.value.trim() || audioTitle);
        }

        // Link to existing source text
        if (this.loadedSourceTextId) {
            formData.append('source_text_id', this.loadedSourceTextId);
        }

        this.els.btnGenerate.disabled = true;
        this.els.btnGenerate.textContent = 'Starting...';

        try {
            const resp = await fetch('/api/synthesize', {
                method: 'POST',
                body: formData,
            });
            const data = await resp.json();

            if (data.error) {
                this.showError(data.error);
                this.resetButton();
                return;
            }

            this.jobId = data.job_id;
            this.totalChunks = data.total_chunks;
            this.startTime = Date.now();

            this.els.progressSection.hidden = false;
            this.els.progressChunks.textContent = '0 / ' + this.totalChunks;
            this.els.progressBar.style.width = '0%';
            this.els.progressTime.textContent = 'Estimating...';

            this.pollInterval = setInterval(() => this.checkStatus(), 1000);

        } catch (err) {
            this.showError('Failed to connect to server: ' + err.message);
            this.resetButton();
        }
    }

    async checkStatus() {
        try {
            const resp = await fetch('/api/status/' + this.jobId);
            const data = await resp.json();

            if (data.error && data.status === 'error') {
                clearInterval(this.pollInterval);
                this.showError('Generation failed: ' + data.error);
                this.els.progressSection.hidden = true;
                this.resetButton();
                return;
            }

            const completed = data.completed_chunks;
            const total = data.total_chunks;
            const pct = total > 0 ? (completed / total) * 100 : 0;

            this.els.progressBar.style.width = pct + '%';
            this.els.progressChunks.textContent = completed + ' / ' + total;

            if (completed > 0) {
                const elapsed = (Date.now() - this.startTime) / 1000;
                const avgPerChunk = elapsed / completed;
                const remaining = avgPerChunk * (total - completed);
                this.els.progressTime.textContent = this.formatTime(remaining) + ' remaining';
            }

            if (data.status === 'complete') {
                clearInterval(this.pollInterval);
                this.els.progressSection.hidden = true;
                this.els.resultSection.hidden = false;
                this.els.audioPlayer.src = '/api/stream/' + this.jobId;
                this.els.audioPlayer.load();
                this.resetButton();

                // Refresh source texts list in case text was saved
                if (this.els.saveTextCheck.checked) {
                    this.loadSourceTexts();
                    this.els.saveTextCheck.checked = false;
                    this.els.saveTextTitle.hidden = true;
                }
            }

        } catch (err) {
            // Network hiccup; keep polling
        }
    }

    formatTime(seconds) {
        if (seconds < 60) return Math.ceil(seconds) + 's';
        const mins = Math.floor(seconds / 60);
        const secs = Math.ceil(seconds % 60);
        return mins + 'm ' + secs + 's';
    }

    resetButton() {
        this.els.btnGenerate.disabled = false;
        this.els.btnGenerate.textContent = 'Generate Audio';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new StorytellerApp();
});
