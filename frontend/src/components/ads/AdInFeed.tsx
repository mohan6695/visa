"use client"

interface AdInFeedProps {
  slotId: string
  className?: string
}

export function AdInFeed({ slotId, className = '' }: AdInFeedProps) {
  return (
    <div className={`ad-in-feed ${className} my-8`}>
      <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
        <ins
          className="adsbygoogle"
          style={{ display: 'block', width: '100%', height: '250px' }}
          data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
          data-ad-slot={slotId}
          data-ad-format="fluid"
          data-ad-layout-key="-gw-3+1f-3b+1c"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `(adsbygoogle = window.adsbygoogle || []).push({});`,
          }}
        />
      </div>
    </div>
  )
}
