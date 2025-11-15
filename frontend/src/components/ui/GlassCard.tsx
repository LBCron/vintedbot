import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '../../lib/utils';

interface GlassCardProps extends Omit<HTMLMotionProps<"div">, "children"> {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
  noPadding?: boolean;
}

export function GlassCard({
  children,
  className,
  hover = false,
  gradient = false,
  noPadding = false,
  ...props
}: GlassCardProps) {
  return (
    <motion.div
      className={cn(
        "relative backdrop-blur-xl bg-white/5 border border-white/10 rounded-2xl",
        "shadow-[0_20px_50px_rgba(0,0,0,0.3)]",
        !noPadding && "p-6",
        hover && "transition-all duration-300 hover:bg-white/8 hover:shadow-[0_30px_60px_rgba(0,0,0,0.4)] hover:scale-[1.02] cursor-pointer",
        gradient && "bg-gradient-to-br from-white/10 to-white/5",
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
