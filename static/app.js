document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    
    // Views
    const viewLanding = document.getElementById('view-landing');
    const viewLoading = document.getElementById('view-loading');
    const viewDashboard = document.getElementById('view-dashboard');
    
    // Landing
    const analyzeForm = document.getElementById('analyze-form');
    const urlInput = document.getElementById('repo-url-input');
    const tryBtns = document.querySelectorAll('.try-btn');
    
    // Loading
    const loadingRepoDisplay = document.getElementById('loading-repo-display');
    const loadingStatusText = document.getElementById('loading-status-text');
    
    // Dashboard Tabs
    const tabLinks = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');
    
    // Dashboard Content
    const dashRepoName = document.getElementById('dash-repo-name');
    const dashTechPills = document.getElementById('dash-tech-pills');
    const dashReportContent = document.getElementById('dash-report-content');
    const dashEntryPoints = document.getElementById('dash-entry-points');
    const dashModuleMap = document.getElementById('dash-module-map');
    const dashDataFlow = document.getElementById('dash-data-flow');
    const dashCaveats = document.getElementById('dash-caveats');
    
    // Metric cards
    const metricTotalFiles = document.getElementById('metric-total-files');
    const metricLanguages = document.getElementById('metric-languages');
    const metricLangBreakdown = document.getElementById('metric-lang-breakdown');
    const metricLoc = document.getElementById('metric-loc');
    const metricDeps = document.getElementById('metric-deps');
    
    // Dashboard Actions
    const btnClear = document.getElementById('btn-clear');
    const btnNewAnalysis = document.getElementById('btn-new-analysis');
    
    // Search
    const searchInput = document.getElementById('search-input');
    const btnSearch = document.getElementById('btn-search');
    const searchResults = document.getElementById('search-results');
    
    let currentRepoName = '';
    let currentRepoShortName = '';
    
    // --- View Navigation ---
    function showView(viewId) {
        viewLanding.classList.add('hidden');
        viewLoading.classList.add('hidden');
        viewDashboard.classList.add('hidden');
        
        viewLanding.classList.remove('flex');
        viewLoading.classList.remove('flex');
        viewDashboard.classList.remove('flex');

        const target = document.getElementById(viewId);
        target.classList.remove('hidden');
        target.classList.add('flex');
    }

    function resetApp() {
        urlInput.value = '';
        currentRepoName = '';
        currentRepoShortName = '';
        
        // Reset steps
        document.querySelectorAll('.step-item').forEach(step => {
            step.classList.remove('opacity-100');
            step.classList.add('opacity-50');
            const icon = step.querySelector('.step-icon');
            icon.classList.remove('border-accent');
            icon.innerHTML = `<span class="material-symbols-outlined text-sm">radio_button_unchecked</span>`;
        });
        
        loadingStatusText.textContent = "Connecting to intelligence engine...";
        
        showView('view-landing');
    }

    // --- Tab Navigation ---
    tabLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Re-style links
            tabLinks.forEach(l => {
                l.classList.remove('bg-primary-container/10', 'border-l-2', 'border-accent', 'text-accent');
                l.classList.add('text-on-surface-variant');
            });
            link.classList.add('bg-primary-container/10', 'border-l-2', 'border-accent', 'text-accent');
            link.classList.remove('text-on-surface-variant');
            
            // Show content
            const targetId = link.getAttribute('href').substring(1);
            tabContents.forEach(c => {
                c.classList.add('hidden');
                c.classList.remove('block');
            });
            document.getElementById('tab-' + targetId).classList.add('block');
            document.getElementById('tab-' + targetId).classList.remove('hidden');
        });
    });

    // --- Actions ---
    tryBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            urlInput.value = btn.textContent.trim();
        });
    });

    btnClear.addEventListener('click', resetApp);
    btnNewAnalysis.addEventListener('click', resetApp);

    // --- WebSocket Logic ---
    analyzeForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) return;

        // Strip url to get name
        try {
            const parsed = new URL(url);
            const pathParts = parsed.pathname.split('/').filter(Boolean);
            if (pathParts.length >= 2) {
                currentRepoName = `${pathParts[0]}/${pathParts[1].replace('.git', '')}`;
                currentRepoShortName = pathParts[1].replace('.git', '');
            } else {
                currentRepoName = pathParts[0] || url;
                currentRepoShortName = currentRepoName;
            }
        } catch {
            currentRepoName = url;
            currentRepoShortName = url;
        }

        loadingRepoDisplay.textContent = 'github.com/' + currentRepoName;
        showView('view-loading');
        
        startAnalysis(url);
    });

    function setStepState(nodeName, state) {
        const step = document.getElementById('step-' + nodeName);
        if (!step) return;
        
        const iconInfo = step.querySelector('.step-icon');
        
        if (state === 'active') {
            step.classList.remove('opacity-50');
            step.classList.add('opacity-100');
            iconInfo.classList.add('border-accent', 'text-accent');
            iconInfo.innerHTML = `<span class="material-symbols-outlined text-sm spinner">autorenew</span>`;
            loadingStatusText.textContent = `Executing node: ${nodeName}`;
        } else if (state === 'done') {
            step.classList.remove('opacity-50');
            step.classList.add('opacity-100');
            iconInfo.classList.replace('border-outline-variant/30', 'border-emerald-500');
            iconInfo.classList.replace('border-accent', 'border-emerald-500');
            iconInfo.classList.add('bg-emerald-500/10', 'text-emerald-500');
            iconInfo.innerHTML = `<span class="material-symbols-outlined text-sm">check</span>`;
        }
    }

    function startAnalysis(url) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/analyze`;
        const ws = new WebSocket(wsUrl);

        const nodeOrder = [
            'parse_structure', 'identify_tech_stack', 'find_entry_points', 
            'summarize_modules', 'trace_data_flow', 'extract_caveats', 'compile_report'
        ];
        let currentNodeIdx = -1;

        ws.onopen = () => {
            ws.send(JSON.stringify({ repo_url: url }));
            setStepState(nodeOrder[0], 'active');
            currentNodeIdx = 0;
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.type === 'error') {
                alert('Analysis Error: ' + data.message);
                resetApp();
                return;
            }
            
            if (data.type === 'progress') {
                const nodeName = data.node;
                const idx = nodeOrder.indexOf(nodeName);
                
                if (idx !== -1) {
                    if (currentNodeIdx !== -1 && currentNodeIdx < nodeOrder.length) {
                        setStepState(nodeOrder[currentNodeIdx], 'done');
                    }
                    if (idx + 1 < nodeOrder.length) {
                        setStepState(nodeOrder[idx + 1], 'active');
                        currentNodeIdx = idx + 1;
                    } else if (idx === nodeOrder.length - 1) {
                         setStepState(nodeOrder[idx], 'done');
                    }
                }
            }
            
            if (data.type === 'complete') {
                finalizeDashboard(data.state);
                setTimeout(() => showView('view-dashboard'), 1000);
            }
        };

        ws.onclose = () => {
             console.log("WS connection closed");
        };
    }

    // --- Dashboard Rendering ---
    function finalizeDashboard(state) {
        dashRepoName.textContent = currentRepoName;
        
        // Store repo short name from server for search
        if (state.repo_name) {
            currentRepoShortName = state.repo_name;
        }
        
        // Render tech pills
        dashTechPills.innerHTML = '';
        if (state.tech_stack) {
            const ts = state.tech_stack;
            const items = [ts.primary_language, ts.framework, ts.database].filter(Boolean);
            items.forEach((item, idx) => {
                const colors = ['bg-[#304671] text-[#9fb5e7]', 'bg-emerald-900/50 text-emerald-400', 'bg-purple-900/50 text-purple-400'];
                const color = colors[idx % colors.length];
                dashTechPills.innerHTML += `<span class="${color} px-2.5 py-0.5 rounded text-xs font-mono border border-white/5">${item}</span>`;
            });
        }

        // Render dynamic metrics
        if (state.metrics) {
            const m = state.metrics;
            if (metricTotalFiles) metricTotalFiles.textContent = m.total_files?.toLocaleString() || '—';
            if (metricLanguages) metricLanguages.textContent = m.languages || '—';
            if (metricLangBreakdown) metricLangBreakdown.textContent = m.lang_breakdown || 'N/A';
            if (metricLoc) metricLoc.textContent = m.loc?.toLocaleString() || '—';
            if (metricDeps) metricDeps.textContent = m.dependencies || '0';
        }

        // Render Markdown content
        if (state.report) dashReportContent.innerHTML = marked.parse(state.report);
        if (state.entry_points) dashEntryPoints.innerHTML = marked.parse(state.entry_points);
        if (state.module_summaries) dashModuleMap.innerHTML = marked.parse(state.module_summaries);
        if (state.data_flow) dashDataFlow.innerHTML = marked.parse(state.data_flow);
        if (state.caveats) dashCaveats.innerHTML = marked.parse(state.caveats);
    }

    // --- Search Logic ---
    btnSearch.addEventListener('click', async () => {
        const query = searchInput.value.trim();
        if(!query) return;
        
        btnSearch.innerHTML = `<span class="material-symbols-outlined spinner">autorenew</span> Searching...`;
        searchResults.innerHTML = '';
        
        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repo_name: currentRepoShortName, 
                    query: query 
                })
            });
            const data = await res.json();
            
            if (data.error) {
                searchResults.innerHTML = `<div class="text-error p-4">${data.error}</div>`;
            } else if (data.documents && data.documents[0] && data.documents[0].length > 0) {
                const docs = data.documents[0];
                const metas = data.metadatas[0];
                
                docs.forEach((doc, idx) => {
                    const file = metas[idx].file || 'Unknown File';
                    searchResults.innerHTML += `
                        <div class="bg-surface-container border border-outline-variant/10 rounded-lg p-4">
                            <div class="flex items-center gap-2 mb-3 text-xs font-mono text-accent">
                                <span class="material-symbols-outlined text-[16px]">description</span>
                                ${file}
                            </div>
                            <pre class="bg-surface-container-lowest p-3 rounded text-sm overflow-x-auto text-on-surface-variant font-mono border border-outline-variant/5"><code>${doc.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>
                        </div>
                    `;
                });
            } else {
                searchResults.innerHTML = `<div class="text-on-surface-variant p-4 text-center">No structural matches found in the codebase.</div>`;
            }
        } catch (e) {
            searchResults.innerHTML = `<div class="text-error p-4">Error executing semantic search: ${e.message}</div>`;
        }
        
        btnSearch.innerHTML = `Query`;
    });
    
    // Allow Enter key in search
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            btnSearch.click();
        }
    });
});
