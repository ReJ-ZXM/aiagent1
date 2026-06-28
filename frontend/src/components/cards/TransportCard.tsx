import type { TransportLeg } from '../../types'

interface Props {
  transport: { to: TransportLeg; back: TransportLeg }
}

export default function TransportCard({ transport }: Props) {
  return (
    <div className="card-travel p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🚄</span>
        <span className="text-sm font-bold text-gray-700">交通方案</span>
      </div>
      <div className="space-y-2">
        <TransportRow leg={transport.to} label="去程" icon="🟢" />
        <div className="border-t border-dashed border-gray-200 my-2" />
        <TransportRow leg={transport.back} label="返程" icon="🔴" />
      </div>
      <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center">
        <span className="text-xs text-gray-400">往返合计</span>
        <span className="font-bold text-travel-600 text-lg">
          ¥{((transport.to?.price || 0) + (transport.back?.price || 0)).toLocaleString()}
        </span>
      </div>
    </div>
  )
}

function TransportRow({ leg, label, icon }: { leg: TransportLeg; label: string; icon: string }) {
  if (!leg) return null
  return (
    <div className="flex items-center gap-3 text-sm bg-gray-50 rounded-xl p-3">
      <span className="text-xs font-bold text-gray-500 bg-white rounded-lg px-2 py-1 border">
        {icon} {label}
      </span>
      <span className="font-mono font-bold text-gray-800">{leg.number}</span>
      <span className="text-gray-400 text-xs">{leg.type}</span>
      <div className="ml-auto text-right">
        <div className="text-xs text-gray-400">{leg.from} → {leg.to}</div>
        <div className="text-xs text-gray-500">{leg.departure} — {leg.arrival}</div>
      </div>
      <span className="font-bold text-sunset-500 text-base">¥{leg.price}</span>
    </div>
  )
}
