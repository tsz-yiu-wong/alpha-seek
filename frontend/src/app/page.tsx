import { Button } from "@/components/ui/button";
import { redirect } from 'next/navigation';

export default function HomePage() {
  redirect('/dashboard');
  
}
