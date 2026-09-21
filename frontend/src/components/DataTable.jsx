import { useMemo, useState } from 'react';

/**
 * Sortable table; scrolls horizontally on narrow screens.
 * @param {{ columns: { key: string, header: string, value?: (row) => any,
 *   render?: (row) => any, sortable?: boolean }[], rows: object[], caption: string,
 *   initialSort?: { key: string, dir: 'asc'|'desc' } }} props
 */
export default function DataTable({ columns, rows, caption, initialSort }) {
  const [sort, setSort] = useState(initialSort ?? { key: columns[0].key, dir: 'asc' });

  const sorted = useMemo(() => {
    const column = columns.find((c) => c.key === sort.key);
    const value = column?.value ?? ((row) => row[sort.key]);
    const direction = sort.dir === 'asc' ? 1 : -1;
    return [...rows].sort((a, b) => {
      const x = value(a);
      const y = value(b);
      return (typeof x === 'string' ? x.localeCompare(y) : x - y) * direction;
    });
  }, [rows, columns, sort]);

  const toggle = (key) =>
    setSort((current) => ({
      key,
      dir: current.key === key && current.dir === 'desc' ? 'asc' : 'desc',
    }));

  return (
    <div className="-mx-5 overflow-x-auto sm:mx-0">
      <table className="w-full min-w-[44rem] text-left text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="border-b border-line">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className="whitespace-nowrap px-3 py-2 font-medium text-muted first:pl-5 sm:first:pl-3"
                aria-sort={
                  sort.key === column.key
                    ? sort.dir === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : undefined
                }
              >
                {column.sortable === false ? (
                  column.header
                ) : (
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 hover:text-ink"
                    onClick={() => toggle(column.key)}
                  >
                    {column.header}
                    <span aria-hidden="true" className="text-xs">
                      {sort.key === column.key ? (sort.dir === 'asc' ? '▲' : '▼') : '↕'}
                    </span>
                  </button>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr key={row.id} className="border-b border-line/70 align-top last:border-0">
              {columns.map((column) => (
                <td key={column.key} className="px-3 py-3 first:pl-5 sm:first:pl-3">
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
