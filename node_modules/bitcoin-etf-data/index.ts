export default async function main() {
    const response = await fetch('https://farside.co.uk/bitcoin-etf-flow-all-data/');
    const html = await response.text();

    const tableRowRegex = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    const cellRegex = /<td[^>]*>([\s\S]*?)<\/td>/gi;
    const data: { date: string; total: number }[] = [];

    let rowMatch;
    while ((rowMatch = tableRowRegex.exec(html)) !== null) {
        const rowHtml = rowMatch[1];
        const cells: string[] = [];

        // Extract cells from the row
        let cellMatch;
        while ((cellMatch = cellRegex.exec(rowHtml)) !== null) {
            cells.push(cellMatch[1]);
        }

        if (cells.length > 0) {
            // First column = date, last column = total
            const dateCell = cells[0];
            const totalCell = cells[cells.length - 1];

            if (dateCell && totalCell) {
                // Remove HTML tags and trim
                const dateText = dateCell.replace(/<[^>]*>/g, '').trim();
                let totalText = totalCell.replace(/<[^>]*>/g, '').trim();

                // Handle negative values (in red and in parentheses)
                if (totalText?.includes('(') && totalText.includes(')')) {
                    totalText = '-' + totalText.replace(/[()]/g, '');
                }

                // Remove commas from numbers
                totalText = totalText?.replace(/,/g, '');

                // Check if it's a valid date (contains numbers and letters)
                if (totalText && dateText && dateText.match(/\d+\s+\w+\s+\d+/) && !isNaN(parseFloat(totalText))) {
                    data.push({
                        date: dateText,
                        total: parseFloat(totalText) * 1_000_000,
                    });
                }
            }
        }
    }

    return data;
}
