export const AnimatedBackground = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-[var(--rm-bg)]" />
      
      {/* Floating orbs */}
      <div 
        className="absolute -top-[40%] -left-[20%] w-[70vw] h-[70vw] rounded-full opacity-[0.07] animate-float"
        style={{
          background: 'radial-gradient(circle, #8B5CF6 0%, transparent 70%)',
          animationDuration: '8s',
        }}
      />
      <div 
        className="absolute -bottom-[30%] -right-[20%] w-[60vw] h-[60vw] rounded-full opacity-[0.05] animate-float"
        style={{
          background: 'radial-gradient(circle, #6D28D9 0%, transparent 70%)',
          animationDuration: '10s',
          animationDelay: '2s',
        }}
      />
      <div 
        className="absolute top-[20%] right-[10%] w-[40vw] h-[40vw] rounded-full opacity-[0.04] animate-float"
        style={{
          background: 'radial-gradient(circle, #A78BFA 0%, transparent 70%)',
          animationDuration: '12s',
          animationDelay: '4s',
        }}
      />
      
      {/* Grid overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(139, 92, 246, 0.3) 1px, transparent 1px),
            linear-gradient(90deg, rgba(139, 92, 246, 0.3) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />
    </div>
  );
};
