# 🪙 bitcoin-etf-data

[![npm downloads](https://img.shields.io/npm/dm/bitcoin-etf-data.svg)](https://www.npmjs.com/package/bitcoin-etf-data)
[![npm](https://img.shields.io/npm/v/bitcoin-etf-data.svg)](https://www.npmjs.com/package/bitcoin-etf-data)
[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

> A fetch-based Node.js/TypeScript scraper that extracts daily Bitcoin ETF data from [farside.co.uk](https://farside.co.uk/btc/).

[📦 **View on NPM**](https://www.npmjs.com/package/bitcoin-etf-data) | [🐛 **Report Issues**](https://github.com/dani69654/bitcoin-etf-data/issues)

## ✨ Features

-   🔄 Scrapes the latest Bitcoin ETF data (date and total) from farside.co.uk
-   📊 Outputs data as an array of objects: `{ date: string, total: number }`
-   🌐 Uses native fetch API for lightweight HTTP requests
-   📱 TypeScript support
-   ⚡ Fast and reliable data extraction
-   🚫 No external dependencies required

## 📦 Installation

```bash
# npm
npm install bitcoin-etf-data

# yarn
yarn add bitcoin-etf-data

# pnpm
pnpm add bitcoin-etf-data
```

## 🔧 Requirements

-   Node.js >= 18 (for native fetch support)

## 🚀 Usage

### Basic Usage

```typescript
import fetchEtfData from 'bitcoin-etf-data';

// Fetch the latest ETF data
const etfData = await fetchEtfData();
console.log(etfData);
```

## 📋 API

### `fetchEtfData(): Promise<Array<{ date: string, total: number }>>`

Makes an HTTP request to farside.co.uk, scrapes the ETF table, and returns an array of objects with `date` and `total` fields.

**Returns:** `Promise<Array<{ date: string, total: number }>>`

**Example Response:**

```typescript
[
    { date: '10 Jul 2025', total: 1175.6 },
    { date: '09 Jul 2025', total: 215.7 },
    { date: '08 Jul 2025', total: 80.1 },
    // ... more entries
];
```

## 📈 Example Output

```json
[
    { "date": "10 Jul 2025", "total": 1175.6 },
    { "date": "09 Jul 2025", "total": 215.7 },
    { "date": "08 Jul 2025", "total": 80.1 },
    { "date": "07 Jul 2025", "total": 216.5 },
    { "date": "03 Jul 2025", "total": 601.8 }
]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

[ISC](https://opensource.org/licenses/ISC)

## ⭐ Support

If this package helped you, please consider giving it a star on [GitHub](https://github.com/dani69654/bitcoin-etf-data)!

---

**Data Source:** [Farside Investors](https://farside.co.uk/btc/) - Bitcoin ETF Flow Data
