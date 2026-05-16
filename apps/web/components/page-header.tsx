type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
};

export function PageHeader({ eyebrow, title, description }: PageHeaderProps) {
  return (
    <section className="mb-8">
      <p className="text-sm font-medium text-blue-700">{eyebrow}</p>
      <h1 className="mt-2 text-3xl font-semibold tracking-normal text-slate-950 sm:text-4xl">
        {title}
      </h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600 sm:text-base">
        {description}
      </p>
    </section>
  );
}
