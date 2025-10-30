"use client";

import Link from "next/link";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/AuthContext";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Music, Upload, FileText, Zap, Users, Star, X } from "lucide-react";
import { Header } from "@/components/ui/header";

export default function LandingPage() {
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const { user, loading } = useAuth();

  // Refs for scroll animations
  const heroRef = useRef<HTMLElement>(null);
  const videoRef = useRef<HTMLElement>(null);
  const featuresRef = useRef<HTMLElement>(null);
  const donationsRef = useRef<HTMLElement>(null);
  const schoolsRef = useRef<HTMLElement>(null);
  const ctaRef = useRef<HTMLElement>(null);

  // Visibility states
  const [heroVisible, setHeroVisible] = useState(false);
  const [videoVisible, setVideoVisible] = useState(false);
  const [featuresVisible, setFeaturesVisible] = useState(false);
  const [donationsVisible, setDonationsVisible] = useState(false);
  const [schoolsVisible, setSchoolsVisible] = useState(false);
  const [ctaVisible, setCtaVisible] = useState(false);

  const logos = [
    "ucla.svg",
    "berklee.svg",
    "uw.png",
    "ubc.png",
    "umich.png",
    "cmu.jpg",
  ];

  useEffect(() => {
    const canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      canonical.setAttribute("href", "https://www.pianofi.ca/");
    }
  }, []);

  useEffect(() => {
    if (user && !loading) {
      setIsRedirecting(true);
      router.push("/dashboard");
    }
  }, [user, loading, router]);

  const handleNavigation = (path: string) => {
    setIsRedirecting(true);
    router.push(path);

    setTimeout(() => {
      setIsRedirecting(false);
    }, 10000);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    handleNavigation("/signup");
  };

  const handleFileInput = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = "audio/*";
    input.onchange = () => {
      handleNavigation("/signup");
    };
    input.click();
  };

  // Scroll animation observer
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -100px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.target === heroRef.current)
          setHeroVisible(entry.isIntersecting);
        if (entry.target === videoRef.current)
          setVideoVisible(entry.isIntersecting);
        if (entry.target === featuresRef.current)
          setFeaturesVisible(entry.isIntersecting);
        if (entry.target === donationsRef.current)
          setDonationsVisible(entry.isIntersecting);
        if (entry.target === schoolsRef.current)
          setSchoolsVisible(entry.isIntersecting);
        if (entry.target === ctaRef.current)
          setCtaVisible(entry.isIntersecting);
      });
    }, observerOptions);

    const refs = [
      heroRef,
      videoRef,
      featuresRef,
      donationsRef,
      schoolsRef,
      ctaRef,
    ];
    refs.forEach((ref) => {
      if (ref.current) observer.observe(ref.current);
    });

    return () => observer.disconnect();
  }, []);

  // IntersectionObserver for video autoplay
  useEffect(() => {
    const video = document.getElementById(
      "landing-demo-video"
    ) as HTMLVideoElement | null;
    if (!video) return;
    const observer = new window.IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            video.play();
          } else {
            video.pause();
          }
        });
      },
      { threshold: 0.5 }
    );
    observer.observe(video);
    return () => observer.disconnect();
  }, []);

  if (isRedirecting) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <Music className="h-12 w-12 text-primary mx-auto mb-4 animate-spin" />
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section
          ref={heroRef}
          className={`w-full h-screen py-12 md:py-24 lg:py-32 xl:py-48 bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background flex items-center justify-center transition-all duration-1000 ${
            heroVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="grid gap-6 lg:grid-cols-[1fr_400px] lg:gap-12 xl:grid-cols-[1fr_600px]">
              <div className="flex flex-col justify-center space-y-4">
                <div className="space-y-2">
                  <Badge variant="secondary" className="w-fit">
                    🎹 AI-Powered Music Transcription
                  </Badge>
                  <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                    Turn Any Song Into
                    <span className="text-primary"> Piano Sheet Music</span>
                  </h1>
                  <p className="max-w-[600px] text-muted-foreground md:text-xl">
                    Upload any audio file - pop songs, instrumentals, classical
                    pieces - and get professional piano sheet music in minutes.
                    Powered by advanced AI models.
                  </p>
                </div>
                <div className="flex flex-col gap-2 min-[400px]:flex-row">
                  <Button size="lg" onClick={() => handleNavigation("/signup")}>
                    Start Converting Music
                  </Button>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span>4.9/5 rating</span>
                  </div>
                  {/* <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    <span>10,000+ musicians</span>
                  </div> */}
                </div>
              </div>
              <div className="flex items-center justify-center">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 rounded-lg blur-3xl opacity-30"></div>
                  <Card className="relative w-full max-w-md">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <Upload className="h-5 w-5" />
                        Upload Your Music
                      </CardTitle>
                      <CardDescription>
                        Drag and drop any audio file to get started
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                          dragActive
                            ? "border-primary bg-primary/5"
                            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-primary/5"
                        }`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={handleFileInput}
                      >
                        <Music className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                        <p className="text-sm text-muted-foreground">
                          MP3, WAV, FLAC supported
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Video Demo Section */}
        <section
          ref={videoRef}
          className={`w-full py-6 md:py-12 transition-all duration-1000 delay-200 ${
            videoVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container px-4 md:px-6 mx-auto">
            <div className="relative w-full max-w-[90vw] mx-auto">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-400 to-blue-400 rounded-3xl blur-3xl opacity-30 -m-4"></div>
              <div className="relative rounded-3xl overflow-hidden shadow-[0_20px_70px_-15px_rgba(0,0,0,0.3)]">
                <div className="aspect-video bg-black/5">
                  <video
                    id="landing-demo-video"
                    src="/pianofi demo_v1 - Made with Clipchamp.mp4"
                    className="w-full h-full object-contain bg-white dark:bg-black"
                    muted
                    playsInline
                    loop
                    autoPlay
                  >
                    Your browser does not support the video tag.
                  </video>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section
          ref={featuresRef}
          id="features"
          className={`w-full py-12 md:py-24 lg:py-32 transition-all duration-1000 delay-300 ${
            featuresVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center mb-12">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">
                  How PianoFi Works
                </h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Our AI-powered platform makes music transcription simple and
                  accurate
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
              {/* Left Column - Large Card */}
              <Card className="flex flex-col">
                <CardHeader>
                  <CardTitle className="text-2xl">Get Sheet Music</CardTitle>
                  <CardDescription className="text-base">
                    Download professional piano sheet music instantly in Midi,
                    PDF, XML with editable notation and multiple difficulty
                    levels.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex-1">
                  <div className="w-full h-[320px] md:h-[550px] rounded-lg overflow-hidden bg-muted">
                    <img
                      src="/transcription_example.png"
                      alt="Dashboard preview"
                      className="w-full h-full object-cover"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Right Column - Two Stacked Cards */}
              <div className="flex flex-col gap-6">
                <Card className="flex-1">
                  <CardHeader>
                    <CardTitle className="text-2xl">
                      State-of-the-art Models for Instant AI Transcriptions
                    </CardTitle>
                    <CardDescription className="text-base">
                      <p>
                        Choose from multiple transcription models tuned for
                        different styles and tasks — fast, reliable, and
                        continually improving.
                      </p>
                      <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                        <li>• Real-time processing</li>
                        <li>• 95%+ accuracy on common genres</li>
                        <li>• Handles complex harmonies &amp; polyphony</li>
                      </ul>
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Placeholder for image */}
                    <div className="w-full h-[70px] md:h-[120px] rounded-lg overflow-hidden bg-muted">
                      <img
                        src="/models.png"
                        alt="model preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </CardContent>
                </Card>

                <Card className="flex-1">
                  <CardHeader>
                    <CardTitle className="text-2xl">Upload Any Audio</CardTitle>
                    <CardDescription className="text-base">
                      Upload any audio file or youtube link - from pop songs to
                      rap to classical pieces
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* Placeholder for image */}
                    <div className="w-full h-[80px] md:h-[130px] rounded-lg overflow-hidden bg-muted">
                      <img
                        src="/upload.png"
                        alt="model preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section
        <section
          id="pricing"
          className="w-full py-12 md:py-24 lg:py-32 bg-muted/50"
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-5xl">
                  Simple Pricing
                </h2>
                <p className="max-w-[900px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Choose the plan that works for you
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl items-center gap-6 py-12 lg:grid-cols-4 lg:gap-12">
              <Card>
                <CardHeader>
                  <CardTitle>Free Trial</CardTitle>
                  <CardDescription>
                    Get started with a free transcription
                  </CardDescription>
                  <div className="text-3xl font-bold">
                    $0<span className="text-sm font-normal">/month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li>• Basic model (still better than our competitors)</li>
                    <li>• 1 transcription per account</li>
                    <li>• Up to 1 minutes per file</li>
                  </ul>
                  <Button
                    onClick={() => handleNavigation("/signup")}
                    className="w-full mt-6"
                  >
                    Get Started
                  </Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Starter</CardTitle>
                  <CardDescription>
                    Perfect for trying out PianoFi
                  </CardDescription>
                  <div className="text-3xl font-bold">
                    $9<span className="text-sm font-normal">/month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li>
                      • Access to the most advanced SOTA transcription models
                    </li>
                    <li>• 10 transcriptions per month</li>
                    <li>• Up to 5 minutes per file</li>
                    <li>• PDF + MusicXML downloads</li>
                    <li>• Email support</li>
                  </ul>
                  <Button
                    onClick={() => handleNavigation("/signup")}
                    className="w-full mt-6"
                  >
                    Get Started
                  </Button>
                </CardContent>
              </Card>
              <Card className="border-primary">
                <CardHeader>
                  <Badge className="w-fit">Most Popular</Badge>
                  <CardTitle>Pro</CardTitle>
                  <CardDescription>
                    For serious musicians and teachers
                  </CardDescription>
                  <div className="text-3xl font-bold">
                    $29<span className="text-sm font-normal">/month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li>• 100 transcriptions per month</li>
                    <li>• Up to 10 minutes per file</li>
                    <li>• PDF + MusicXML downloads</li>
                    <li>• Priority support</li>
                    <li>• Batch processing</li>
                  </ul>
                  <Button
                    onClick={() => handleNavigation("/signup")}
                    className="w-full mt-6"
                  >
                    Get Started
                  </Button>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Enterprise</CardTitle>
                  <CardDescription>
                    For music schools and studios
                  </CardDescription>
                  <div className="text-3xl font-bold">
                    $99<span className="text-sm font-normal">/month</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li>• Unlimited transcriptions</li>
                    <li>• No file length limits</li>
                    <li>• All formats included</li>
                    <li>• Dedicated support</li>
                    <li>• API access</li>
                  </ul>
                  <Button className="w-full mt-6">Contact Sales</Button>
                </CardContent>
              </Card>
            </div>
          </div>
        </section> */}

        {/* Schools / Partners Section */}
        <section
          ref={schoolsRef}
          className={`w-full py-12 md:py-24 lg:py-32 bg-white dark:bg-background transition-all duration-1000 delay-400 ${
            schoolsVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center text-center mb-6">
              <h2 className="text-2xl sm:text-3xl font-bold">
                Musicians on PianoFi come from
              </h2>
              <p className="max-w-[800px] text-muted-foreground mt-2">
                We work with musicians and students from top music schools and
                universities.
              </p>
            </div>

            <style>{`
              @keyframes scroll {
                0% {
                  transform: translateX(0);
                }
                100% {
                  transform: translateX(-50%);
                }
              }
            `}</style>
            <div className="overflow-hidden mt-6">
              <div
                style={{
                  display: "flex",
                  gap: "3rem",
                  alignItems: "center",
                  animation: "scroll 30s linear infinite",
                }}
              >
                {[...logos, ...logos].map((f, i) => (
                  <img
                    key={`${f}-${i}`}
                    src={`/logos/${f}`}
                    alt={f.replace(/\..*/, "")}
                    className="h-14 md:h-20 lg:h-24"
                    style={{
                      flexShrink: 0,
                      width: "auto",
                      display: "block",
                    }}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Donations Section */}
        <section
          ref={donationsRef}
          className={`w-full py-12 md:py-24 lg:py-32 bg-muted/50 transition-all duration-1000 delay-400 ${
            donationsVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">
                  Support PianoFi
                </h2>
                <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed">
                  Help us continue improving our AI music transcription
                  technology and keep building amazing features for musicians
                  everywhere.
                </p>
              </div>
              <div className="space-y-4">
                <Button size="lg" asChild>
                  <a
                    href="https://ko-fi.com/pianofi"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center"
                  >
                    <span>☕</span>
                    <span className="ml-2">Support us on Ko-fi</span>
                  </a>
                </Button>
                <p className="text-sm text-muted-foreground">
                  Every contribution helps us make PianoFi better for everyone
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section
          ref={ctaRef}
          className={`w-full py-12 md:py-24 lg:py-32 transition-all duration-1000 delay-500 ${
            ctaVisible
              ? "opacity-100 translate-y-0"
              : "opacity-0 translate-y-10"
          }`}
        >
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl md:text-5xl">
                  Ready to Transform Your Music?
                </h2>
                <p className="mx-auto max-w-[600px] text-muted-foreground md:text-xl/relaxed lg:text-base/relaxed xl:text-xl/relaxed">
                  Join thousands of musicians who trust PianoFi for accurate
                  music transcription
                </p>
              </div>
              <div className="space-x-4">
                <Button size="lg" onClick={() => handleNavigation("/signup")}>
                  Start Transcribing!
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="w-full shrink-0 border-t">
        <div className="container mx-auto px-4 md:px-6 py-6 flex flex-col sm:flex-row items-center gap-2">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} PianoFi. All rights reserved.
          </p>
          <nav className="sm:ml-auto flex gap-4 sm:gap-6">
            <Link
              href="/terms"
              className="text-xs hover:underline underline-offset-4"
            >
              Terms of Service
            </Link>
            <Link
              href="/privacy"
              className="text-xs hover:underline underline-offset-4"
            >
              Privacy Policy
            </Link>
            <Link
              href="/contact"
              className="text-xs hover:underline underline-offset-4"
            >
              Contact
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
