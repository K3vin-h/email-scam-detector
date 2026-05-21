const now = new Date();
const daysAgo = (n) => new Date(now - n * 86400000).toISOString();

export const DEMO_STATS = {
  total_scanned: 248,
  total_scams: 31,
  scams_last_7_days: 5,
  scams_last_30_days: 18,
  top_scam_senders: [
    'alerts@paypa1-secure.com',
    'no-reply@amaz0n-verify.net',
    'support@apple-id-locked.com',
    'billing@netf1ix-update.io',
    'security@bankofamer1ca.co',
  ],
};

export const DEMO_EMAILS = [
  {
    id: 1,
    gmail_id: 'demo_001',
    sender: 'alerts@paypa1-secure.com',
    subject: 'Your PayPal account has been limited — verify now',
    snippet: 'We noticed unusual activity on your account. Please verify your identity immediately to avoid suspension.',
    received_at: daysAgo(0.2),
    scanned_at: daysAgo(0.1),
    confidence: 0.97,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Suspicious sender domain', 'Urgency language', 'Phishing keywords'],
    user_risk_override: null,
  },
  {
    id: 2,
    gmail_id: 'demo_002',
    sender: 'no-reply@amaz0n-verify.net',
    subject: 'Action Required: Update your payment method',
    snippet: 'Your Amazon order could not be processed. Click here to update your payment details within 24 hours.',
    received_at: daysAgo(0.5),
    scanned_at: daysAgo(0.4),
    confidence: 0.94,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Lookalike domain', 'Payment phishing', 'Fake deadline'],
    user_risk_override: null,
  },
  {
    id: 3,
    gmail_id: 'demo_003',
    sender: 'noreply@github.com',
    subject: '[GitHub] A third-party OAuth application has been added',
    snippet: 'Hey kevinh! A third-party OAuth application (Claude Code) was recently authorized to access your account.',
    received_at: daysAgo(1),
    scanned_at: daysAgo(0.9),
    confidence: 0.04,
    is_scam: false,
    risk_level: 'legit',
    risk_label: 'Legit',
    reasons: [],
    user_risk_override: null,
  },
  {
    id: 4,
    gmail_id: 'demo_004',
    sender: 'billing@netf1ix-update.io',
    subject: 'Your Netflix subscription will be cancelled',
    snippet: 'We were unable to renew your subscription. Please update your billing info to continue watching.',
    received_at: daysAgo(1.5),
    scanned_at: daysAgo(1.4),
    confidence: 0.91,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Lookalike domain', 'Subscription phishing', 'Urgency language'],
    user_risk_override: null,
  },
  {
    id: 5,
    gmail_id: 'demo_005',
    sender: 'message@e.adobe.com',
    subject: 'Your Creative Cloud subscription receipt',
    snippet: 'Thanks for your purchase. Your Adobe Creative Cloud subscription has been renewed for another year.',
    received_at: daysAgo(2),
    scanned_at: daysAgo(1.9),
    confidence: 0.08,
    is_scam: false,
    risk_level: 'legit',
    risk_label: 'Legit',
    reasons: [],
    user_risk_override: null,
  },
  {
    id: 6,
    gmail_id: 'demo_006',
    sender: 'irs-refund@tax-gov-irs.com',
    subject: 'IRS Tax Refund — Claim your $847.00 refund now',
    snippet: 'The IRS has processed your tax return. You are eligible for a refund of $847.00. Click here to claim.',
    received_at: daysAgo(2.5),
    scanned_at: daysAgo(2.4),
    confidence: 0.99,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Government impersonation', 'Prize/refund bait', 'Suspicious sender domain'],
    user_risk_override: null,
  },
  {
    id: 7,
    gmail_id: 'demo_007',
    sender: 'noreply@osu.edu',
    subject: 'OSU: Registration opens Monday for Fall 2026',
    snippet: 'Undergraduate registration for Fall 2026 opens Monday, May 25 at 7:00 AM. Log in to MyOSU to view your enrollment appointment.',
    received_at: daysAgo(3),
    scanned_at: daysAgo(2.9),
    confidence: 0.06,
    is_scam: false,
    risk_level: 'legit',
    risk_label: 'Legit',
    reasons: [],
    user_risk_override: null,
  },
  {
    id: 8,
    gmail_id: 'demo_008',
    sender: 'support@apple-id-locked.com',
    subject: 'Apple ID Locked — Verify within 48 hours',
    snippet: 'Your Apple ID has been locked due to suspicious activity. Verify your information to unlock your account.',
    received_at: daysAgo(3.5),
    scanned_at: daysAgo(3.4),
    confidence: 0.96,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Apple impersonation', 'Account lockout scare', 'Suspicious sender domain'],
    user_risk_override: null,
  },
  {
    id: 9,
    gmail_id: 'demo_009',
    sender: 'hello@job-offer-network.biz',
    subject: 'You have been selected for a remote work opportunity',
    snippet: 'Congratulations! Based on your LinkedIn profile, you have been selected for a $65/hour remote data entry position.',
    received_at: daysAgo(4),
    scanned_at: daysAgo(3.9),
    confidence: 0.78,
    is_scam: false,
    risk_level: 'possible_scam',
    risk_label: 'Possible scam',
    reasons: ['Unsolicited job offer', 'Too-good-to-be-true salary'],
    user_risk_override: null,
  },
  {
    id: 10,
    gmail_id: 'demo_010',
    sender: 'notifications@slack.com',
    subject: 'Kevin, you have 3 unread messages in #general',
    snippet: 'You have new messages in the scam-filter workspace. Tap to read.',
    received_at: daysAgo(4.5),
    scanned_at: daysAgo(4.4),
    confidence: 0.03,
    is_scam: false,
    risk_level: 'legit',
    risk_label: 'Legit',
    reasons: [],
    user_risk_override: null,
  },
  {
    id: 11,
    gmail_id: 'demo_011',
    sender: 'crypto-rewards@wallet-airdrop.io',
    subject: 'You have unclaimed crypto — 0.35 ETH waiting',
    snippet: 'Your Ethereum wallet is eligible for an airdrop. Connect your wallet now to claim 0.35 ETH before the deadline.',
    received_at: daysAgo(5),
    scanned_at: daysAgo(4.9),
    confidence: 0.93,
    is_scam: true,
    risk_level: 'scam',
    risk_label: 'Scam',
    reasons: ['Crypto airdrop scam', 'Wallet drain attempt', 'Fake deadline'],
    user_risk_override: null,
  },
  {
    id: 12,
    gmail_id: 'demo_012',
    sender: 'receipts@squareup.com',
    subject: 'Your receipt from Blue Bottle Coffee',
    snippet: 'Thanks for your purchase at Blue Bottle Coffee. Total: $6.75. Paid with Visa ending in 4242.',
    received_at: daysAgo(6),
    scanned_at: daysAgo(5.9),
    confidence: 0.05,
    is_scam: false,
    risk_level: 'legit',
    risk_label: 'Legit',
    reasons: [],
    user_risk_override: null,
  },
];

const PAGE_SIZE = 10;

export function filterEmails(emails, riskLevel) {
  if (!riskLevel) return emails;
  return emails.filter((e) => e.risk_level === riskLevel);
}

export function pageEmails(emails, page) {
  const start = (page - 1) * PAGE_SIZE;
  return emails.slice(start, start + PAGE_SIZE);
}

// ─── Settings ────────────────────────────────────────────────────────────────

export const DEMO_SETTINGS = {
  scan_window_days: 7,
  scan_frequency_hours: 6,
  notify_frequency: 'daily',
  notify_via_email: true,
  notify_email_address: 'placeholder@example.com',
  gmail_connected: true,
  gmail_email_address: 'placeholder@example.com',
  gmail_last_sync: daysAgo(0.1),
};

// ─── Daily stats (7-day chart) ───────────────────────────────────────────────

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
export const DEMO_DAILY_STATS = Array.from({ length: 7 }, (_, i) => {
  const d = new Date(now - (6 - i) * 86400000);
  const scanned = [34, 41, 28, 52, 37, 44, 12][i];
  const scams = [3, 5, 2, 8, 4, 6, 3][i];
  return {
    date: d.toISOString().slice(0, 10),
    day: DAYS[d.getDay()],
    scanned,
    scams,
  };
});

// ─── Sender stats (KPI tiles) ────────────────────────────────────────────────

export const DEMO_SENDER_STATS = {
  scam_trend_pct: -12,
  most_impersonated: 'paypal.com',
  highest_risk_sender: 'alerts@paypa1-secure.com',
};

// ─── Reports ─────────────────────────────────────────────────────────────────

export const DEMO_REPORTS = [
  {
    id: 1,
    period: 'daily',
    generated_at: daysAgo(0),
    total_scanned: 12,
    total_scams: 3,
    top_senders: [
      { sender: 'alerts@paypa1-secure.com', count: 2 },
      { sender: 'crypto-rewards@wallet-airdrop.io', count: 1 },
    ],
  },
  {
    id: 2,
    period: 'daily',
    generated_at: daysAgo(1),
    total_scanned: 44,
    total_scams: 6,
    top_senders: [
      { sender: 'billing@netf1ix-update.io', count: 3 },
      { sender: 'no-reply@amaz0n-verify.net', count: 2 },
      { sender: 'support@apple-id-locked.com', count: 1 },
    ],
  },
  {
    id: 3,
    period: 'weekly',
    generated_at: daysAgo(0),
    total_scanned: 248,
    total_scams: 31,
    top_senders: [
      { sender: 'alerts@paypa1-secure.com', count: 8 },
      { sender: 'no-reply@amaz0n-verify.net', count: 7 },
      { sender: 'billing@netf1ix-update.io', count: 6 },
      { sender: 'irs-refund@tax-gov-irs.com', count: 5 },
      { sender: 'support@apple-id-locked.com', count: 5 },
    ],
  },
  {
    id: 4,
    period: 'weekly',
    generated_at: daysAgo(7),
    total_scanned: 312,
    total_scams: 43,
    top_senders: [
      { sender: 'security@bankofamer1ca.co', count: 11 },
      { sender: 'alerts@paypa1-secure.com', count: 9 },
      { sender: 'crypto-rewards@wallet-airdrop.io', count: 8 },
    ],
  },
  {
    id: 5,
    period: 'monthly',
    generated_at: daysAgo(0),
    total_scanned: 1104,
    total_scams: 138,
    top_senders: [
      { sender: 'alerts@paypa1-secure.com', count: 34 },
      { sender: 'no-reply@amaz0n-verify.net', count: 28 },
      { sender: 'billing@netf1ix-update.io', count: 24 },
      { sender: 'irs-refund@tax-gov-irs.com', count: 19 },
      { sender: 'security@bankofamer1ca.co', count: 17 },
    ],
  },
];

export function filterReports(reports, period) {
  if (!period) return reports;
  return reports.filter((r) => r.period === period);
}
