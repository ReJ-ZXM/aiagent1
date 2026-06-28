import type { DayPlan, TripItem } from '../../types'

interface Props { day: DayPlan }

const ICONS: Record<string, string> = {
  attraction: '📍', meal: '🍜', transport: '🚄', hotel: '🏨',
}

const COLORS: Record<string, string> = {
  attraction: 'border-l-travel-400 bg-travel-50/50',
  meal: 'border-l-sunset-400 bg-sunset-50/50',
  transport: 'border-l-ocean-400 bg-ocean-50/50',
  hotel: 'border-l-purple-400 bg-purple-50/50',
}

export default function DayPlanCard({ day }: Props) {
  return (
    <div className="border-l-[3px] border-travel-300 pl-4 py-1">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-bold bg-travel-500 text-white rounded-lg px-2.5 py-1">
          DAY {day.day_number}
        </span>
        <span className="text-sm font-bold text-gray-700">{day.title}</span>
        <span className="text-xs text-gray-400">{day.date}</span>
      </div>
      <div className="space-y-2">
        {day.items?.map((item, i) => (
          <TimelineItem key={i} item={item} icon={ICONS[item.type] || '📍'} color={COLORS[item.type] || ''} />
        ))}
      </div>
    </div>
  )
}

function TimelineItem({ item, icon, color }: { item: TripItem; icon: string; color: string }) {
  return (
    <div className={`flex gap-3 text-sm border border-gray-100 rounded-xl p-3 ${color}`}>
      <span className="shrink-0 text-base">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start">
          <span className="font-medium text-gray-800 truncate">{item.title}</span>
          {item.cost > 0 && <span className="text-sunset-500 font-bold shrink-0 ml-2">¥{item.cost}</span>}
        </div>
        <div className="flex gap-2 text-xs text-gray-400 mt-1">
          {item.start && <span className="font-mono">{item.start}</span>}
          {item.start && item.end && <span>→</span>}
          {item.end && <span className="font-mono">{item.end}</span>}
          {item.description && <span className="truncate text-gray-500">· {item.description}</span>}
        </div>
      </div>
    </div>
  )
}
