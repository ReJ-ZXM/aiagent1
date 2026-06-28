import type { TransportLeg } from '../../types'
import { getTransportBookingUrl } from '../../lib/bookingUrl'

interface Props {
  transport: { to: TransportLeg; back: TransportLeg }
}

export default function TransportCard({ transport }: Props) {
  const totalPrice = (transport.to?.price || 0) + (transport.back?.price || 0)

  return (
    <div className="card-travel p-4">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-travel-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <span className="text-sm font-bold text-gray-700">交通方案</span>
      </div>
      <div className="space-y-2">
        <TransportRow leg={transport.to} label="去程" />
        <div className="border-t border-dashed border-gray-200 my-2" />
        <TransportRow leg={transport.back} label="返程" />
      </div>
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
        <span className="text-xs text-gray-400">往返合计</span>
        <span className="font-bold text-travel-600 text-lg">
          ¥{totalPrice.toLocaleString()}
        </span>
      </div>
    </div>
  )
}

function TransportRow({ leg, label }: { leg: TransportLeg; label: string }) {
  if (!leg) return null
  const isGo = label === '去程'
  const booking = getTransportBookingUrl(leg.type)

  return (
    <div className="flex items-center gap-3 text-sm bg-gray-50 rounded-xl p-3 flex-wrap">
      <span className={`text-xs font-bold bg-white rounded-lg px-2 py-1 border ${isGo ? 'text-emerald-600 border-emerald-200' : 'text-rose-600 border-rose-200'}`}>
        {label}
      </span>
      <span className="font-mono font-bold text-gray-800">{leg.number}</span>
      <span className="text-gray-400 text-xs">{leg.type}</span>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-gray-400">{leg.from} → {leg.to}</div>
        <div className="text-xs text-gray-500">{leg.departure} — {leg.arrival}</div>
      </div>
      <span className="font-bold text-sunset-500 text-base">¥{leg.price}</span>
      <a
        href={booking.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-xs font-medium text-white bg-travel-500 hover:bg-travel-600 transition rounded-lg px-3 py-1.5 shrink-0 no-underline"
      >
        {booking.label}
        <span className="ml-1 opacity-70 text-[10px]">@{booking.platform}</span>
      </a>
    </div>
  )
}
