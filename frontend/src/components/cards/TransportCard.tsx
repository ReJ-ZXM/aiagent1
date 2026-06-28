import type { TransportLeg } from '../../types'

interface Props {
  transport: {
    to: TransportLeg
    back: TransportLeg
  }
}

export default function TransportCard({ transport }: Props) {
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm space-y-3">
      <h3 className="text-sm font-bold flex items-center gap-2">
        <span>🚂</span> 交通方案
      </h3>
      <TransportRow leg={transport.to} label="去程" />
      <div className="border-t border-dashed" />
      <TransportRow leg={transport.back} label="返程" />
      <div className="text-right text-sm text-gray-500">
        交通合计: <span className="font-bold text-gray-800">
          ¥{((transport.to?.price || 0) + (transport.back?.price || 0)).toLocaleString()}
        </span>
      </div>
    </div>
  )
}

function TransportRow({ leg, label }: { leg: TransportLeg; label: string }) {
  if (!leg) return null
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-medium">{label}</span>
      <span className="font-mono font-bold">{leg.number}</span>
      <span className="text-gray-600">{leg.type}</span>
      <span className="ml-auto text-gray-500">{leg.from} {leg.departure} → {leg.to} {leg.arrival}</span>
      <span className="font-bold text-orange-600">¥{leg.price}</span>
    </div>
  )
}
