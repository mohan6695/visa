"use client"

interface AdSidebarProps {
  slotId: string
  position: 'left' | 'right'
}

export function AdSidebar({ slotId, position = 'right' }: AdSidebarProps) {
  return (
    <div className={`ad-sidebar ad-sidebar-${position} fixed top-20 ${position}-4 w-[160px] h-[600px] hidden lg:block z-40`}>
      <ins
        className="adsbygoogle"
        style={{ display: 'inline-block', width: '160px', height: '600px' }}
        data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
        data-ad-slot={slotId}
        data-ad-format="vertical"
        data-full-width-responsive="true"
      />
      <script
        dangerouslySetInnerHTML={{
          __html: `(adsbygoogle = window.adsbygoogle || []).push({});`,
        }}
      />
    </div>
  )
}
