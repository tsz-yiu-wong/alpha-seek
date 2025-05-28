import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <div className="container relative">
      <section className="mx-auto flex max-w-[980px] flex-col items-center gap-2 py-8 md:py-12 md:pb-8 lg:py-24 lg:pb-20">
        <h1 className="text-center text-3xl font-heading leading-tight tracking-tighter md:text-6xl lg:leading-[1.1]">
          Welcome to Alpha Seek
        </h1>
        <p className="max-w-[750px] text-center text-lg text-muted-foreground sm:text-xl">
          Your AI-powered agent for navigating the DeFi landscape. Automated trading and advanced strategy system at your fingertips.
        </p>
        <div className="flex w-full items-center justify-center space-x-4 py-4 md:pb-10">
          <Button asChild>
            <a href="/trading">Get Started with Trading</a>
          </Button>
          <Button variant="outline" asChild>
            <a href="/strategies">Explore Strategies</a>
          </Button>
        </div>
      </section>
    </div>
  );
}
