interface AdBannerProps {
  slotId: string;
  format?: 'horizontal' | 'vertical';
  className?: string;
}

export default function AdBanner({ slotId, format = 'horizontal', className = '' }: AdBannerProps) {
  return (
    <div className={`ad-banner ${className}`}>
      <div className="ad-placeholder h-[90px] flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-600">Ad Banner - {slotId}</p>
      </div>
    </div>
  );
}
