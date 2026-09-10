import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card } from './ui.jsx'
import { useReducedMotion } from '../hooks/useReducedMotion.js'
import { MACRO_ROWS, SERIES, formatNumber, shortDayLabel } from '../lib/macros.js'

const AXIS = { stroke: '#64748b', fontSize: 12 }
const GRID = '#26303d'
const SURFACE = '#121821'

function TooltipShell({ title, rows }) {
  return (
    <div className="rounded-lg border border-line bg-surface px-3 py-2 text-xs shadow-xl">
      <p className="mb-1.5 font-semibold text-white">{title}</p>
      <ul className="space-y-1">
        {rows.map((row) => (
          <li key={row.label} className="flex items-center gap-2">
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: row.color }}
              aria-hidden="true"
            />
            <span className="text-slate-400">{row.label}</span>
            <span className="ml-auto font-medium text-slate-100">{row.value}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Daily intake against goal, one horizontal bar per macro.
 *
 * Each bar is its own entity, so the goal is drawn as a track behind the fill
 * rather than as a second series — one axis, no stacking, and the number is
 * direct-labelled so identity never rests on colour alone.
 */
export function MacroProgressBars({ totals, goals }) {
  const rows = MACRO_ROWS.map((row) => {
    const consumed = Number(totals?.[row.key]) || 0
    const goal = Number(goals?.[row.key]) || 0
    const percent = goal > 0 ? (consumed / goal) * 100 : 0
    return { ...row, consumed, goal, percent, over: goal > 0 && consumed > goal }
  })

  return (
    <ul className="space-y-4">
      {rows.map((row) => (
        <li key={row.key}>
          <div className="mb-1.5 flex items-baseline justify-between gap-3 text-sm">
            <span className="flex items-center gap-2 font-medium text-slate-200">
              <span
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: row.color }}
                aria-hidden="true"
              />
              {row.label}
            </span>
            <span className="text-slate-400">
              <span className="font-semibold text-white">{formatNumber(row.consumed, 0)}</span>
              {' / '}
              {formatNumber(row.goal, 0)} {row.unit}
              <span className={`ml-2 ${row.over ? 'text-warn' : 'text-slate-500'}`}>
                {Math.round(row.percent)}%
              </span>
            </span>
          </div>

          <div
            className="h-2.5 w-full overflow-hidden rounded-full bg-surface-2"
            role="progressbar"
            aria-label={`${row.label}: ${formatNumber(row.consumed, 0)} of ${formatNumber(row.goal, 0)} ${row.unit}`}
            aria-valuenow={Math.round(row.consumed)}
            aria-valuemin={0}
            aria-valuemax={Math.round(row.goal) || 100}
          >
            <div
              className="h-full rounded-full transition-[width] duration-500"
              style={{
                width: `${Math.min(row.percent, 100)}%`,
                backgroundColor: row.color,
              }}
            />
          </div>

          {row.over ? (
            <p className="mt-1 text-xs text-warn">
              {formatNumber(row.consumed - row.goal, 0)} {row.unit} over your goal
            </p>
          ) : null}
        </li>
      ))}
    </ul>
  )
}

/** Today's macro split as bars — a quick shape check, one bar per macro. */
export function MacroSplitChart({ totals }) {
  const reducedMotion = useReducedMotion()
  const data = MACRO_ROWS.filter((row) => row.key !== 'calories').map((row) => ({
    name: row.label,
    value: Number(totals?.[row.key]) || 0,
    color: row.color,
  }))

  const empty = data.every((entry) => entry.value === 0)

  return (
    <div className="h-56">
      {empty ? (
        <div className="flex h-full items-center justify-center text-sm text-slate-500">
          Log a food to see today&apos;s split.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
            <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} tick={AXIS} />
            <YAxis tickLine={false} axisLine={false} tick={AXIS} width={44} unit="g" />
            <Tooltip
              cursor={{ fill: '#ffffff0d' }}
              content={({ active, payload }) =>
                active && payload?.length ? (
                  <TooltipShell
                    title={payload[0].payload.name}
                    rows={[
                      {
                        label: 'Today',
                        value: `${formatNumber(payload[0].value, 1)} g`,
                        color: payload[0].payload.color,
                      },
                    ]}
                  />
                ) : null
              }
            />
            <Bar
              dataKey="value"
              radius={[4, 4, 0, 0]}
              maxBarSize={48}
              isAnimationActive={!reducedMotion}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} stroke={SURFACE} strokeWidth={2} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

const TREND_VIEWS = {
  calories: {
    label: 'Calories',
    series: [{ key: 'calories', name: 'Calories', color: SERIES.calories, unit: 'kcal' }],
    goalKey: 'calories',
    unit: 'kcal',
  },
  macros: {
    label: 'Protein / Carbs / Fats',
    series: [
      { key: 'protein_g', name: 'Protein', color: SERIES.protein, unit: 'g' },
      { key: 'carbs_g', name: 'Carbs', color: SERIES.carbs, unit: 'g' },
      { key: 'fats_g', name: 'Fats', color: SERIES.fats, unit: 'g' },
    ],
    goalKey: null,
    unit: 'g',
  },
}

/**
 * Trailing trend, one line per series on a single shared axis.
 *
 * Calories and grams are never mixed onto two y-scales — the toggle switches
 * between them instead, which is why there is no second axis anywhere here.
 */
export function MacroTrendChart({ trend, days = 7 }) {
  const [view, setView] = useState('calories')
  const reducedMotion = useReducedMotion()
  const config = TREND_VIEWS[view]

  const data = useMemo(
    () =>
      (trend?.points || []).map((point) => ({
        ...point,
        label: shortDayLabel(point.day),
      })),
    [trend],
  )

  const goal = config.goalKey ? Number(trend?.goals?.[config.goalKey]) || 0 : 0

  return (
    <Card className="p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-semibold text-white">Last {days} days</h3>
          <p className="text-xs text-slate-500">
            Days with nothing logged are shown as zero, not skipped.
          </p>
        </div>
        <div className="flex gap-1 rounded-lg border border-line bg-surface-2 p-1" role="tablist">
          {Object.entries(TREND_VIEWS).map(([key, option]) => (
            <button
              key={key}
              role="tab"
              aria-selected={view === key}
              onClick={() => setView(key)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${
                view === key ? 'bg-accent-strong text-ink' : 'text-slate-400 hover:text-white'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 12, right: 24, left: -12, bottom: 0 }}>
            <CartesianGrid stroke={GRID} strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="label" tickLine={false} axisLine={false} tick={AXIS} />
            <YAxis tickLine={false} axisLine={false} tick={AXIS} width={52} />
            <Tooltip
              cursor={{ stroke: '#475569', strokeWidth: 1 }}
              content={({ active, payload, label }) =>
                active && payload?.length ? (
                  <TooltipShell
                    title={label}
                    rows={config.series.map((series) => {
                      const entry = payload.find((item) => item.dataKey === series.key)
                      return {
                        label: series.name,
                        value: `${formatNumber(entry?.value ?? 0, 0)} ${series.unit}`,
                        color: series.color,
                      }
                    })}
                  />
                ) : null
              }
            />

            {goal > 0 ? (
              <ReferenceLine
                y={goal}
                stroke="#64748b"
                strokeDasharray="5 4"
                ifOverflow="extendDomain"
                label={{
                  value: `Goal ${formatNumber(goal, 0)}`,
                  position: 'insideTopRight',
                  fill: '#94a3b8',
                  fontSize: 11,
                }}
              />
            ) : null}

            {/* A single series is named by the heading, so no legend box for it. */}
            {config.series.length > 1 ? (
              <Legend
                verticalAlign="bottom"
                height={28}
                iconType="plainline"
                wrapperStyle={{ fontSize: 12, color: '#94a3b8' }}
              />
            ) : null}

            {config.series.map((series) => (
              <Line
                key={series.key}
                type="monotone"
                dataKey={series.key}
                name={series.name}
                stroke={series.color}
                strokeWidth={2}
                dot={{ r: 4, fill: series.color, stroke: SURFACE, strokeWidth: 2 }}
                activeDot={{ r: 6, stroke: SURFACE, strokeWidth: 2 }}
                isAnimationActive={!reducedMotion}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
