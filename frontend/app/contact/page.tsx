"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Mail, MessageSquare, Clock } from "lucide-react";
import { Header } from "@/components/ui/header";

export default function ContactPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="w-full py-12 md:py-24 lg:py-32 bg-gradient-to-br from-purple-50 to-blue-50 dark:bg-none dark:from-transparent dark:to-transparent dark:bg-background">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <Badge variant="secondary" className="w-fit">
                  🎹 Get in Touch
                </Badge>
                <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                  Contact
                  <span className="text-primary"> PianoFi</span>
                </h1>
                <p className="max-w-[600px] text-muted-foreground md:text-xl">
                  Have questions about music transcription? Need help with your
                  account? We're here to help you make beautiful music.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section className="w-full py-6 md:py-12 lg:py-16 pb-24 md:pb-48 lg:pb-60">
          <div className="container mx-auto px-4 md:px-6">
            <div className="max-w-4xl mx-auto">
              <div className="space-y-6 text-center mb-12">
                <h2 className="text-3xl font-bold tracking-tighter">
                  Let's Talk Music
                </h2>
                <p className="text-muted-foreground max-w-2xl mx-auto">
                  Reach out to us directly via email. We typically respond
                  within 24 hours and are here to help with any questions about
                  PianoFi.
                </p>
              </div>

              <div className="grid gap-6 md:grid-cols-3">
                <Card className="text-center">
                  <CardHeader>
                    <Mail className="h-12 w-12 text-primary mx-auto mb-4" />
                    <CardTitle>Email Us</CardTitle>
                    <CardDescription>
                      For general inquiries and support
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <a
                        href="mailto:jonathan@pianofi.ca"
                        className="text-primary hover:underline font-medium text-lg block"
                      >
                        jonathan@pianofi.ca
                      </a>
                      <a
                        href="mailto:bruce@pianofi.ca"
                        className="text-primary hover:underline font-medium text-lg block"
                      >
                        bruce@pianofi.ca
                      </a>
                    </div>
                  </CardContent>
                </Card>

                <Card className="text-center">
                  <CardHeader>
                    <Clock className="h-12 w-12 text-primary mx-auto mb-4" />
                    <CardTitle>Response Time</CardTitle>
                    <CardDescription>
                      When you can expect to hear from us
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm">
                      We typically respond within 24 hours during business days.
                      For urgent issues, please mark your email as "URGENT".
                    </p>
                  </CardContent>
                </Card>

                <Card className="text-center">
                  <CardHeader>
                    <MessageSquare className="h-12 w-12 text-primary mx-auto mb-4" />
                    <CardTitle>What We Can Help With</CardTitle>
                    <CardDescription>
                      Areas where we provide support
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ul className="text-sm space-y-1 text-left">
                      <li>• Technical support and troubleshooting</li>
                      <li>• Account and billing questions</li>
                      <li>• Feature requests and feedback</li>
                      <li>• Partnership and business inquiries</li>
                      <li>• Music transcription questions</li>
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ Section */}
        <section className="w-full py-12 md:py-24 lg:py-32 bg-muted/50">
          <div className="container mx-auto px-4 md:px-6">
            <div className="flex flex-col items-center justify-center space-y-4 text-center">
              <div className="space-y-2">
                <h2 className="text-3xl font-bold tracking-tighter sm:text-4xl">
                  Frequently Asked Questions
                </h2>
                <p className="max-w-[600px] text-muted-foreground md:text-xl/relaxed">
                  Quick answers to common questions about PianoFi
                </p>
              </div>
            </div>
            <div className="mx-auto grid max-w-5xl gap-6 py-12 lg:grid-cols-2 lg:gap-12">
              <Card>
                <CardHeader>
                  <CardTitle>How accurate is the transcription?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Our AI models achieve 95%+ accuracy on most audio files.
                    Complex polyphonic pieces may require minor manual
                    adjustments.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>What audio formats do you support?</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    We support MP3, WAV, FLAC, and most common audio formats.
                    For best results, use high-quality audio files.
                  </p>
                </CardContent>
              </Card>
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
            <a
              href="/terms"
              className="text-xs hover:underline underline-offset-4"
            >
              Terms of Service
            </a>
            <a
              href="/privacy"
              className="text-xs hover:underline underline-offset-4"
            >
              Privacy Policy
            </a>
            <a
              href="/contact"
              className="text-xs hover:underline underline-offset-4"
            >
              Contact
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}
