import { motion } from 'framer-motion';

export const TypingIndicator = () => {
  return (
    <div className="flex items-center gap-4 px-4 py-6 md:px-6">
      <div className="mx-auto flex flex-1 gap-4 md:max-w-3xl lg:max-w-[40rem] xl:max-w-[48rem]">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg">
            <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z" />
              <path d="M12 14c-4 0-7 2-7 4v2h14v-2c0-2-3-4-7-4z" />
            </svg>
          </div>
        </div>

        {/* Dots */}
        <div className="flex items-center gap-1.5 pt-2">
          {[0, 1, 2].map(i => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-[var(--rm-text-muted)]"
              animate={{
                opacity: [0.3, 1, 0.3],
                y: [0, -4, 0],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.15,
                ease: 'easeInOut',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};
