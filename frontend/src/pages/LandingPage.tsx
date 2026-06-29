import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, GitBranch, Brain, Shield, Sparkles, Code2, FileSearch } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { RepoMindLogo } from '../components/ui/RepoMindLogo';
import { AnimatedBackground } from '../components/ui/AnimatedBackground';

export const LandingPage = () => {
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Analysis',
      description: 'Understand complex codebases instantly with intelligent context-aware analysis.',
      gradient: 'from-violet-500 to-purple-600',
    },
    {
      icon: FileSearch,
      title: 'Deep Code Exploration',
      description: 'Navigate architecture, find patterns, and understand dependencies at a glance.',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Shield,
      title: 'Security & Quality',
      description: 'Identify vulnerabilities, suggest improvements, and generate documentation.',
      gradient: 'from-emerald-500 to-teal-500',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col relative overflow-auto">
      <AnimatedBackground />

      {/* Nav */}
      <motion.nav
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex items-center justify-between px-6 md:px-12 py-5"
      >
        <RepoMindLogo size="md" />
        <div className="flex items-center gap-3">
          <Link to="/login">
            <Button variant="ghost" size="sm">Sign In</Button>
          </Link>
          <Link to="/signup">
            <Button size="sm">Get Started</Button>
          </Link>
        </div>
      </motion.nav>

      {/* Hero */}
      <div className="flex-1 flex flex-col items-center justify-center relative z-10 px-6 py-16 md:py-24">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
          className="text-center max-w-3xl mx-auto"
        >
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2, duration: 0.4 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--rm-accent)]/10 border border-[var(--rm-accent)]/20 text-[var(--rm-accent)] text-sm font-medium mb-8"
          >
            <Sparkles className="w-4 h-4" />
            AI-Powered Repository Intelligence
          </motion.div>

          {/* Heading */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
            Understand, explore and{' '}
            <span className="bg-gradient-to-r from-[#8B5CF6] via-[#A78BFA] to-[#6D28D9] bg-clip-text text-transparent">
              improve
            </span>{' '}
            any GitHub repository with AI
          </h1>

          {/* Subtitle */}
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="text-lg md:text-xl text-[var(--rm-text-secondary)] max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            RepoMind uses advanced RAG to analyze any GitHub repository — ask questions, 
            review architecture, find security issues, and generate documentation in seconds.
          </motion.p>

          {/* CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.4 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/signup">
              <Button size="lg" variant="accent" className="min-w-[180px]">
                Create Account
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="min-w-[180px]">
                Sign In
              </Button>
            </Link>
          </motion.div>

          {/* Tech badges */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
            className="flex items-center justify-center gap-6 mt-12 text-[var(--rm-text-muted)] text-sm"
          >
            <div className="flex items-center gap-2">
              <GitBranch className="w-4 h-4" />
              <span>Any GitHub repo</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-[var(--rm-text-muted)]" />
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4" />
              <span>All languages</span>
            </div>
            <div className="w-1 h-1 rounded-full bg-[var(--rm-text-muted)]" />
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4" />
              <span>Secure & private</span>
            </div>
          </motion.div>
        </motion.div>
      </div>

      {/* Features */}
      <div className="relative z-10 px-6 md:px-12 pb-20">
        <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
                className="group p-6 rounded-2xl bg-[var(--rm-surface)]/60 border border-[var(--rm-border)] hover:border-[var(--rm-border-active)] transition-all duration-300 hover:shadow-glow"
              >
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4 shadow-lg`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="text-lg font-semibold mb-2 text-[var(--rm-text)]">{feature.title}</h3>
                <p className="text-sm text-[var(--rm-text-secondary)] leading-relaxed">{feature.description}</p>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-[var(--rm-border)] px-6 py-6 text-center text-sm text-[var(--rm-text-muted)]">
        © {new Date().getFullYear()} RepoMind. Built with AI for developers.
      </footer>
    </div>
  );
};
