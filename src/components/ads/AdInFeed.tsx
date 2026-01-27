interface AdInFeedProps {
  slotId: string;
  className?: string;
}

export default function AdInFeed({ slotId, className = '' }: AdInFeedProps) {
  return (
    <div className={`ad-infeed ${className}`}>
      <div className="ad-placeholder h-[250px] flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-600">In-Feed Ad - {slotId}</p>
      </div>
    </div>
  );
}
