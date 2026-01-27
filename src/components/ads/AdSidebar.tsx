interface AdSidebarProps {
  slotId: string;
  position: 'left' | 'right';
  className?: string;
}

export default function AdSidebar({ slotId, position, className = '' }: AdSidebarProps) {
  return (
    <div className={`ad-sidebar ${position}-sidebar ${className}`}>
      <div className="ad-placeholder h-[250px] flex items-center justify-center bg-gray-100 rounded-lg">
        <p className="text-gray-600">Sidebar Ad - {slotId}</p>
      </div>
    </div>
  );
}
