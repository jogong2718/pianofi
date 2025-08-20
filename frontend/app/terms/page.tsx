"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/ui/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Scale,
  FileText,
  Shield,
  AlertTriangle,
  Mail,
  Users,
} from "lucide-react";

export default function TermsOfServicePage() {
  const [lastUpdated, setLastUpdated] = useState("");

  useEffect(() => {
    // Set the date on the client side to avoid hydration mismatch
    setLastUpdated(new Date().toLocaleDateString());
  }, []);

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
                  <Scale className="h-4 w-4 mr-2" />
                  Legal Terms
                </Badge>
                <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                  Terms of Service
                </h1>
                <p className="max-w-[600px] text-muted-foreground md:text-xl">
                  Please read these terms carefully before using PianoFi's AI
                  music transcription service.
                </p>
                {lastUpdated && (
                  <p className="text-sm text-muted-foreground">
                    Last updated: {lastUpdated}
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Terms Content */}
        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container mx-auto px-4 md:px-6">
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Acceptance of Terms */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    Acceptance of Terms
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    By accessing or using PianoFi's AI music transcription
                    service, you agree to be bound by these Terms of Service and
                    our Privacy Policy. If you do not agree to these terms,
                    please do not use our service.
                  </p>
                  <p className="text-muted-foreground">
                    We reserve the right to modify these terms at any time.
                    Changes will be effective immediately upon posting to our
                    website.
                  </p>
                </CardContent>
              </Card>

              {/* Service Description */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-primary" />
                    Service Description
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    PianoFi provides AI-powered music transcription services
                    that convert audio files into piano sheet music in various
                    formats including PDF, MusicXML, and MIDI.
                  </p>
                  <div>
                    <h3 className="font-semibold mb-2">Service Features</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Audio file upload and processing (MP3, WAV, FLAC)</li>
                      <li>AI-powered music transcription</li>
                      <li>Sheet music generation in multiple formats</li>
                      <li>File storage and download capabilities</li>
                      <li>User account management</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* User Accounts */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    User Accounts and Responsibilities
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Account Registration</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>
                        You must provide accurate and complete information
                      </li>
                      <li>
                        You are responsible for maintaining account security
                      </li>
                      <li>One account per person or entity</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Acceptable Use</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Use the service only for lawful purposes</li>
                      <li>
                        Do not upload copyrighted material without permission
                      </li>
                      {/* <li>Do not attempt to reverse engineer our AI models</li> */}
                      <li>
                        Do not use the service to harm others or our systems
                      </li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Intellectual Property */}
              <Card>
                <CardHeader>
                  <CardTitle>Intellectual Property Rights</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Your Content</h3>
                    <p className="text-muted-foreground">
                      You retain ownership of audio files you upload. By using
                      our service, you grant us a limited license to process
                      your files for transcription purposes only.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Our Service</h3>
                    <p className="text-muted-foreground">
                      PianoFi owns all rights to our software, and generated
                      transcriptions. The transcribed sheet music is provided to
                      you for your personal or commercial use.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Copyright Compliance</h3>
                    <p className="text-muted-foreground">
                      You are responsible for ensuring you have the right to
                      upload and transcribe any audio content. We will respond
                      to valid DMCA takedown notices.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Payment Terms */}
              {/* <Card>
                <CardHeader>
                  <CardTitle>Payment and Subscription Terms</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Subscription Plans</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Subscription fees are billed monthly in advance</li>
                      <li>
                        All fees are non-refundable except as required by law
                      </li>
                      <li>We may change pricing with 30 days notice</li>
                      <li>
                        Cancellations take effect at the end of the current
                        billing period
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Usage Limits</h3>
                    <p className="text-muted-foreground">
                      Each subscription plan includes specific usage limits.
                      Exceeding these limits may result in additional charges or
                      service restrictions.
                    </p>
                  </div>
                </CardContent>
              </Card> */}

              {/* Service Availability */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-primary" />
                    Service Availability and Disclaimers
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Service Availability</h3>
                    <p className="text-muted-foreground">
                      We strive for 99.9% uptime but cannot guarantee
                      uninterrupted service. We may perform maintenance that
                      temporarily affects availability.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">
                      AI Accuracy Disclaimer
                    </h3>
                    <p className="text-muted-foreground">
                      Our AI transcription service aims for high accuracy but
                      cannot guarantee perfect results. Transcription quality
                      may vary based on audio quality and complexity.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Data Backup</h3>
                    <p className="text-muted-foreground">
                      While we maintain backups, you are responsible for keeping
                      copies of important files. We are not liable for data
                      loss.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Limitation of Liability */}
              <Card>
                <CardHeader>
                  <CardTitle>Limitation of Liability</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    TO THE MAXIMUM EXTENT PERMITTED BY LAW, PIANOFI SHALL NOT BE
                    LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, OR
                    CONSEQUENTIAL DAMAGES ARISING FROM YOUR USE OF THE SERVICE.
                  </p>
                </CardContent>
              </Card>

              {/* Termination */}
              <Card>
                <CardHeader>
                  <CardTitle>Termination</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">By Us</h3>
                    <p className="text-muted-foreground">
                      We may suspend or terminate your account for violations of
                      these terms, non-payment, or other reasons at our
                      discretion.
                    </p>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">
                      Effect of Termination
                    </h3>
                    <p className="text-muted-foreground">
                      Upon termination, your access to the service will cease
                      and your files may be deleted after a reasonable period.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Governing Law */}
              <Card>
                <CardHeader>
                  <CardTitle>Governing Law and Disputes</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    These terms are governed by the laws of the jurisdiction
                    where PianoFi is incorporated. Any disputes will be resolved
                    through binding arbitration or in the courts of that
                    jurisdiction.
                  </p>
                  <p className="text-muted-foreground">
                    If any provision of these terms is found unenforceable, the
                    remaining provisions will continue in full force and effect.
                  </p>
                </CardContent>
              </Card>

              {/* Contact Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-primary" />
                    Contact Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    If you have questions about these Terms of Service, please
                    contact us:
                  </p>
                  <div className="space-y-2 text-muted-foreground">
                    <p>
                      Email:{" "}
                      <a
                        href="mailto:jonathan@pianofi.ca"
                        className="text-primary hover:underline"
                      >
                        jonathan@pianofi.ca
                      </a>
                    </p>
                    <p>
                      Email:{" "}
                      <a
                        href="mailto:bruce@pianofi.ca"
                        className="text-primary hover:underline"
                      >
                        bruce@pianofi.ca
                      </a>
                    </p>
                  </div>
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
