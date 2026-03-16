// RPC 配置
// 使用 Helius DAS API 节点获取 Metaplex Core 资产数据
const RPC_ENDPOINT = "https://mainnet.helius-rpc.com/?api-key=236b88d9-ac4e-4da5-9361-c17b6b9661a4";

// 徽章数据
const badgesData = [
    {
        id: "newcomer",
        name: "新人徽章",
        points: 100,
        address: "Cpy7V4GKHVbJaVchR5qKPANtccjVC5bBbtabZJX6E2gT",
        holders: null // 初始为 null，等待 RPC 加载
    },
    {
        id: "researcher",
        name: "研究员徽章",
        points: 5000,
        address: "7oXuyGZAUzmij4c76uz9TvM2seDcsRWP1zhfLMJfRdyk",
        holders: null
    },
    {
        id: "scholar",
        name: "学者徽章",
        points: 10000,
        address: "7AEpoq5eKoSRUN36CTFFPQESDXepcSby7CfQZs44wgds",
        holders: null
    },
    {
        id: "speed_demon",
        name: "Speed Demon",
        points: "???", // 暂未提供积分数值
        address: "5RgA8Vo6FnnAzre12JsLicoc66B7h8cwG99RRPFGTAgj",
        holders: null
    },
    {
        id: "human_captcha",
        name: "Human CAPTCHA",
        points: "已验证",
        address: "DB1HvGZNTyRjQvoQfBLFVojpnSBzEwNKrFH4bMZD3uZb",
        holders: 43273, // 数据更新时间：2026-03-14 (需要手动更新)
        skipFetch: true
    }
];

// 获取代币持有者数量 (支持 DAS API for Metaplex Core)
async function fetchHolderCount(collectionAddress) {
    try {
        // 策略1: 优先尝试获取 Collection Asset 本身的 mpl_core_info
        // 对于 Metaplex Core Collection，getAsset 返回的 mpl_core_info.current_size 即为当前铸造总量
        const assetResponse = await fetch(RPC_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "getAsset",
                params: {
                    id: collectionAddress
                }
            })
        });

        if (assetResponse.ok) {
            const assetData = await assetResponse.json();
            if (assetData.result && assetData.result.mpl_core_info) {
                const size = assetData.result.mpl_core_info.current_size;
                if (size !== undefined) {
                    return size;
                }
            }
        }

        // 策略2: 如果策略1失败，回退到 getAssetsByGroup
        const response = await fetch(RPC_ENDPOINT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: "2.0",
                id: 1,
                method: "getAssetsByGroup",
                params: {
                    groupKey: "collection",
                    groupValue: collectionAddress,
                    page: 1,
                    limit: 1
                }
            })
        });

        if (!response.ok) return null; // 网络错误，保持默认值

        const data = await response.json();
        
        // DAS API 响应处理
        if (data.result && data.result.total) {
            return data.result.total;
        }
        
        return null; // 无法获取真实数据，保持默认值

    } catch (error) {
        console.warn(`Fetch failed for ${collectionAddress}:`, error);
        return null;
    }
}

// 格式化日期
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    }).format(date);
}

// 格式化数字
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

// 复制功能
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        alert('地址已复制到剪贴板！');
    }).catch(err => {
        console.error('无法复制文本: ', err);
    });
}

// 渲染徽章列表
async function renderBadges() {
    const badgeList = document.getElementById('badgeList');
    if (!badgeList) return;

    // 初始渲染（显示 Loading，如果是静态数据则直接显示）
    badgeList.innerHTML = badgesData.map(badge => generateBadgeHTML(badge, !badge.skipFetch)).join('');

    // 尝试异步更新真实数据
    for (let i = 0; i < badgesData.length; i++) {
        const badge = badgesData[i];
        
        // 如果标记为跳过 fetching，则直接使用预设值
        if (badge.skipFetch) {
            continue;
        }

        // 只有当 RPC 有效时才覆盖默认值
        const realHolders = await fetchHolderCount(badge.address);
        
        if (realHolders !== null) {
            badgesData[i].holders = realHolders;
            // 更新 DOM
            const badgeCard = badgeList.querySelector(`.badge-card.${badge.id}`);
            if (badgeCard) {
                const countElement = badgeCard.querySelector('.holders-count');
                if (countElement) {
                    countElement.textContent = formatNumber(realHolders);
                    countElement.classList.remove('loading-text');
                }
            }
        } else {
             // 如果获取失败，显示暂无数据
            const badgeCard = badgeList.querySelector(`.badge-card.${badge.id}`);
            if (badgeCard) {
                const countElement = badgeCard.querySelector('.holders-count');
                if (countElement) {
                    countElement.textContent = '暂无数据';
                    countElement.classList.remove('loading-text');
                }
            }
        }
    }
}

// 生成徽章 HTML
function generateBadgeHTML(badge, isLoading = false) {
    const holdersDisplay = isLoading ? '<span class="loading-text">加载中...</span>' : (badge.holders !== null ? formatNumber(badge.holders) : '暂无数据');
    
    // 处理积分显示逻辑，如果是数字则加"积分"，否则直接显示文本
    const pointsDisplay = typeof badge.points === 'number' ? `${badge.points} 积分` : badge.points;

    return `
        <div class="badge-card ${badge.id}">
            <div class="badge-header">
                <h3>${badge.name}</h3>
                <span class="points-tag">${pointsDisplay}</span>
            </div>
            <div class="badge-body">
                <div class="holders-info">
                    <span class="holders-label">👥 持有地址人数</span>
                    <span class="holders-count ${isLoading ? 'loading-text' : ''}">${holdersDisplay}</span>
                </div>
                <p class="contract-label">合约地址</p>
                <div class="contract-address">
                    <code>${badge.address}</code>
                    <button class="copy-btn" onclick="copyToClipboard('${badge.address}')">复制</button>
                </div>
            </div>
        </div>
    `;
}

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 优先从 window.BADGE_HISTORY 中获取 Human CAPTCHA 的最新数据
    if (window.BADGE_HISTORY && window.BADGE_HISTORY.length > 0) {
        const latestData = window.BADGE_HISTORY[window.BADGE_HISTORY.length - 1];
        if (latestData && latestData.human_captcha !== undefined) {
            const humanCaptchaBadge = badgesData.find(b => b.id === 'human_captcha');
            if (humanCaptchaBadge) {
                humanCaptchaBadge.holders = latestData.human_captcha;
            }
        }
    }

    await renderBadges();
    await renderGrowthChart(); // 改为 async 以支持 fetch
});

// 获取历史数据（优先从全局变量读取，其次尝试 fetch，最后 mock）
async function fetchHistoryData() {
    // 1. 尝试读取全局变量 (由 js/badge_data.js 提供，支持 file:// 协议)
    if (window.BADGE_HISTORY && Array.isArray(window.BADGE_HISTORY)) {
        console.log("Loaded history data from global variable.");
        return window.BADGE_HISTORY;
    }

    // 2. 尝试 fetch (仅在 http/https 环境下有效)
    try {
        const response = await fetch('badge_stats.json');
        if (response.ok) {
            const data = await response.json();
            return data;
        }
    } catch (error) {
        console.warn("Failed to fetch badge_stats.json, falling back to mock data:", error);
    }
    return null;
}

// 生成模拟历史数据 (兜底逻辑)
function generateMockHistory(finalValue, days = 30) {
    // ... 保持原有模拟逻辑不变，仅在无真实数据时使用 ...
    const data = [];
    let currentValue = finalValue || 0;
    
    if (!finalValue) return Array(days).fill(0);

    for (let i = 0; i < days; i++) {
        data.unshift(currentValue);
        const growthRate = 0.005 + Math.random() * 0.015;
        const decrease = Math.floor(currentValue * growthRate);
        currentValue = Math.max(0, currentValue - decrease);
    }
    return data;
}

// 渲染增长趋势图表
async function renderGrowthChart() {
    const ctx = document.getElementById('growthChart');
    if (!ctx) return;

    // 尝试获取真实历史记录
    const realHistory = await fetchHistoryData();
    
    let labels = [];
    let newcomerData = [];
    let researcherData = [];
    let scholarData = [];
    let isRealData = false;

    if (realHistory && realHistory.length > 0) {
        // 使用真实数据
        isRealData = true;
        
        // 解析真实数据
        labels = realHistory.map(entry => entry.date.slice(5)); // 取 MM-DD
        newcomerData = realHistory.map(entry => entry.newcomer || 0);
        researcherData = realHistory.map(entry => entry.researcher || 0);
        scholarData = realHistory.map(entry => entry.scholar || 0);
        
        // 检查是否需要追加今日实时数据
        const lastEntry = realHistory[realHistory.length - 1];
        const lastDate = lastEntry.date; // YYYY-MM-DD
        
        // 获取今日日期 (YYYY-MM-DD)
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const todayStr = `${year}-${month}-${day}`;
        
        // 如果历史记录的最后一天不是今天，且我们有实时数据，则追加
        if (lastDate !== todayStr) {
            const newcomerLive = badgesData.find(b => b.id === 'newcomer')?.holders;
            const researcherLive = badgesData.find(b => b.id === 'researcher')?.holders;
            const scholarLive = badgesData.find(b => b.id === 'scholar')?.holders;
            
            if (newcomerLive && researcherLive && scholarLive) {
                labels.push(`${month}/${day}`);
                newcomerData.push(newcomerLive);
                researcherData.push(researcherLive);
                scholarData.push(scholarLive);
            }
        }
        
        // 更新提示文案
        const noteEl = document.querySelector('.chart-note');
        if (noteEl) {
             noteEl.innerHTML = `✅ 说明：图表展示了从 ${realHistory[0].date} 开始记录的真实链上快照数据${lastDate !== todayStr ? '及今日实时数据' : ''}。`;
             noteEl.style.color = "#047857";
             noteEl.style.borderColor = "#6ee7b7";
             noteEl.style.backgroundColor = "#ecfdf5";
        }

    } else {
        // 使用模拟数据 (原有逻辑)
        // 准备日期标签 (最近30天)
        for (let i = 29; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            labels.push(`${date.getMonth() + 1}/${date.getDate()}`);
        }

        const newcomerCount = badgesData.find(b => b.id === 'newcomer')?.holders || 73000;
        const researcherCount = badgesData.find(b => b.id === 'researcher')?.holders || 32000;
        const scholarCount = badgesData.find(b => b.id === 'scholar')?.holders || 5000;

        newcomerData = generateMockHistory(newcomerCount);
        researcherData = generateMockHistory(researcherCount);
        scholarData = generateMockHistory(scholarCount);
    }

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '新人徽章',
                    data: newcomerData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '研究员徽章',
                    data: researcherData,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                },
                {
                    label: '学者徽章',
                    data: scholarData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true, // 如果数值很大，可以设为 false 以突出变化
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// --- 批量查询 Human CAPTCHA 功能 ---

// 官方的创作者地址（Human CAPTCHA）
const TARGET_CREATOR = "DB1HvGZNTyRjQvoQfBLFVojpnSBzEwNKrFH4bMZD3uZb";

async function checkWalletForNFT(walletAddress) {
    let page = 1;
    const limit = 1000;
    
    try {
        while (true) {
            // 使用 DAS API 的 getAssetsByOwner 方法
            const response = await fetch(RPC_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    id: `page-${page}`,
                    method: 'getAssetsByOwner',
                    params: {
                        ownerAddress: walletAddress,
                        page: page,
                        limit: limit
                    },
                }),
            });

            if (!response.ok) return { found: false, error: `RPC Error: ${response.status}` };

            const data = await response.json();
            
            if (!data.result || !data.result.items) {
                // 如果第一页就没数据，或者出错
                return { found: false };
            }

            const items = data.result.items;

            // 在当前页的资产中，寻找符合条件的 NFT
            const foundNFT = items.find(asset => {
                // 确保资产有 creators 数组
                if (!asset.creators) return false;
                
                // 核心逻辑：遍历 creators 数组，比对地址并且必须是已验证状态
                return asset.creators.some(creator => 
                    creator.address === TARGET_CREATOR && creator.verified === true
                );
            });

            if (foundNFT) {
                return { 
                    found: true, 
                    name: foundNFT.content?.metadata?.name || 'Human CAPTCHA',
                    id: foundNFT.id 
                };
            }

            // 如果当前页不满，说明没有更多数据了
            if (items.length < limit) {
                break;
            }

            // 否则继续查下一页
            page++;
            
            // 安全限制：防止死循环，最多查 50 页 (5万个资产)
            if (page > 50) break;
        }

        return { found: false };

    } catch (error) {
        console.error(`查询钱包 ${walletAddress} 时出错:`, error);
        return { found: false, error: error.message };
    }
}

// 绑定查询按钮事件
document.addEventListener('DOMContentLoaded', () => {
    const queryBtn = document.getElementById('queryBtn');
    if (queryBtn) {
        queryBtn.addEventListener('click', async () => {
            const textarea = document.getElementById('walletAddresses');
            const resultsContainer = document.getElementById('queryResults');
            const statusDiv = document.getElementById('queryStatus');
            
            if (!textarea || !resultsContainer) return;

            const input = textarea.value.trim();
            if (!input) {
                alert('请输入钱包地址');
                return;
            }

            const wallets = input.split('\n').map(line => line.trim()).filter(line => line.length > 0);
            if (wallets.length === 0) return;

            // 清空旧结果
            resultsContainer.innerHTML = '';
            statusDiv.textContent = `准备查询 ${wallets.length} 个地址...`;
            queryBtn.disabled = true;

            // 1. 先创建所有 UI 占位符
            const uiElements = new Map();
            for (const wallet of wallets) {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.innerHTML = `
                    <span class="wallet-address">${wallet}</span>
                    <span class="nft-status loading">等待查询...</span>
                `;
                resultsContainer.appendChild(resultItem);
                uiElements.set(wallet, resultItem); // 存储引用以便后续更新
            }

            let successCount = 0;
            let processedCount = 0;
            const CONCURRENCY_LIMIT = 5; // 并发限制
            
            const updateUI = (wallet, result) => {
                const resultItem = uiElements.get(wallet);
                if (!resultItem) return;

                const statusSpan = resultItem.querySelector('.nft-status');
                statusSpan.classList.remove('loading');
                
                if (result.found) {
                    resultItem.classList.add('success');
                    statusSpan.classList.add('found');
                    statusSpan.textContent = `✅ 已持有 (${result.name})`;
                    successCount++;
                } else {
                    resultItem.classList.add('failure');
                    statusSpan.classList.add('not-found');
                    statusSpan.textContent = result.error ? `❌ 出错: ${result.error}` : '❌ 未持有';
                }
                
                processedCount++;
                statusDiv.textContent = `正在查询... (${processedCount}/${wallets.length}) - 发现: ${successCount}`;
            };
            
            // 执行并发查询
            await processQueue(wallets, CONCURRENCY_LIMIT, uiElements, updateUI);

            statusDiv.textContent = `查询完成。共查询 ${wallets.length} 个地址，其中 ${successCount} 个持有目标 NFT。`;
            queryBtn.disabled = false;
        });
    }
});

// 并发队列处理器
async function processQueue(items, limit, uiElements, updateCallback) {
    const executing = new Set();
    
    for (const item of items) {
        // 更新 UI 为 "查询中"
        const uiItem = uiElements.get(item);
        if (uiItem) uiItem.querySelector('.nft-status').textContent = "查询中...";

        const p = checkWalletForNFT(item).then(result => {
            updateCallback(item, result);
            return item;
        });
        
        executing.add(p);
        
        // 当 Promise 完成时，从 Set 中移除
        const clean = p.then(() => executing.delete(p));
        
        if (executing.size >= limit) {
            await Promise.race(executing);
        }
    }
    
    // 等待剩余的任务完成
    await Promise.all(executing);
}

// --- Twitter Modal Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('twitterModal');
    const followBtn = document.getElementById('followBtn');
    
    // Check if already followed in this session
    if (!sessionStorage.getItem('twitterFollowed')) {
        // Show modal
        if (modal) {
            modal.style.display = 'flex';
        }
    }

    if (followBtn && modal) {
        followBtn.addEventListener('click', () => {
            // Open Twitter
            window.open('https://x.com/AxinSpark', '_blank');
            
            // Mark as followed and close modal
            sessionStorage.setItem('twitterFollowed', 'true');
            modal.style.display = 'none';
        });
    }
});
