import type { DayPlan, TripItem } from '../../types'

interface Props {
  day: DayPlan
}

export default function DayPlanCard({ day }: Props) {
  const typeIcons: Record<string, string> = {
    attraction: '📍',
    meal: '🍜',
    transport: '🚂',
    hotel: '🏨',
  }

  return (
    <div className="border-l-2 border-blue-200 pl-4 py-1">
      <h4 className="text-sm font-bold text-gray-700 mb-2">
        Day {day.day_number} · {day.date} — {day.title}
      </h4>
      <div className="space-y-2">
        {day.items?.map((item, i) => (
          <TimelineItem key={i} item={item} icon={typeIcons[item.type] || '📍'} />
        ))}
      </div>
    </div>
  )
}

function TimelineItem({ item, icon }: { item: TripItem; icon: string }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between">
          <span className="font-medium truncate">{item.title}</span>
          {item.cost > 0 && <span className="text-orange-500 shrink-0 ml-2">¥{item.cost}</span>}
        </div>
        <div className="flex gap-2 text-xs text-gray-400 mt-0.5">
          {item.start && <span>{item.start}</span>}
          {item.start && item.end && <span>-</span>}
          {item.end && <span>{item.end}</span>}
          {item.description && <span className="truncate">· {item.description}</span>}
        </div>
      </div>
    </div>
  )
}
