"use client"

interface AdBannerProps {
  slotId: string
  format?: 'horizontal' | 'vertical' | 'rectangle'
  className?: string
}

export function AdBanner({ slotId, format = 'horizontal', className = '' }: AdBannerProps) {
  const formatDimensions = {
    horizontal: 'w-full h-[90px]',
    vertical: 'w-[160px] h-[600px]',
    rectangle: 'w-[300px] h-[250px]',
  }

  return (
    <div className={`ad-banner ${formatDimensions[format]} ${className}`}>
      <ins
        className="adsbygoogle"
        style={{ display: 'block' }}
        data-ad-client="ca-pub-YOUR_PUBLISHER_ID"
        data-ad-slot={slotId}
        data-ad-format={format}
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
