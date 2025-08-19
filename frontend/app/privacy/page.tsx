"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/ui/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, Eye, Lock, Users, FileText, Mail } from "lucide-react";

export default function PrivacyPolicyPage() {
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
                  <Shield className="h-4 w-4 mr-2" />
                  Privacy & Security
                </Badge>
                <h1 className="text-3xl font-bold tracking-tighter sm:text-5xl xl:text-6xl/none">
                  Privacy Policy
                </h1>
                <p className="max-w-[600px] text-muted-foreground md:text-xl">
                  We take your privacy seriously. Learn how we collect, use, and
                  protect your data.
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

        {/* Privacy Policy Content */}
        <section className="w-full py-12 md:py-24 lg:py-32">
          <div className="container mx-auto px-4 md:px-6">
            <div className="max-w-4xl mx-auto space-y-8">
              {/* Overview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Eye className="h-5 w-5 text-primary" />
                    Overview
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    At PianoFi, we are committed to protecting your privacy and
                    ensuring the security of your personal information. This
                    Privacy Policy explains how we collect, use, disclose, and
                    safeguard your information when you use our AI-powered music
                    transcription service.
                  </p>
                  <p className="text-muted-foreground">
                    By using PianoFi, you agree to the collection and use of
                    information in accordance with this policy.
                  </p>
                </CardContent>
              </Card>

              {/* Information We Collect */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-primary" />
                    Information We Collect
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h3 className="font-semibold mb-2">Personal Information</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>
                        Email address (for account creation and communication)
                      </li>
                      <li>Name (optional, for personalization)</li>
                      <li>
                        Payment information (processed securely through Stripe)
                      </li>
                      <li>Usage data and preferences</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">Audio Files</h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>Audio files you upload for transcription</li>
                      <li>Generated sheet music and MIDI files</li>
                      <li>
                        Metadata about your files (filename, duration, format)
                      </li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="font-semibold mb-2">
                      Technical Information
                    </h3>
                    <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                      <li>IP address and device information</li>
                      <li>Browser type and version</li>
                      <li>Usage patterns and feature interactions</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* How We Use Your Information */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    How We Use Your Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    We use the information we collect to:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>
                      Provide and maintain our music transcription service
                    </li>
                    <li>Process your audio files and generate sheet music</li>
                    <li>Manage your account and billing</li>
                    <li>Send you service-related communications</li>
                    <li>Improve our AI models and service quality</li>
                    <li>Prevent fraud and ensure platform security</li>
                    <li>Comply with legal obligations</li>
                  </ul>
                </CardContent>
              </Card>

              {/* Data Security */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lock className="h-5 w-5 text-primary" />
                    Data Security
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    We implement appropriate technical and organizational
                    security measures to protect your personal information:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>End-to-end encryption for data transmission</li>
                    <li>Secure cloud storage with AWS</li>
                    <li>Regular security audits and monitoring</li>
                    <li>Access controls and authentication measures</li>
                  </ul>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm">
                      <strong>Note:</strong> Deleting your transcriptions are a
                      soft delete, meaning they are not immediately removed from
                      our servers.
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Data Sharing */}
              <Card>
                <CardHeader>
                  <CardTitle>Information Sharing and Disclosure</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    We do not sell, trade, or otherwise transfer your personal
                    information to third parties, except:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>With your explicit consent</li>
                    <li>
                      To trusted service providers who assist in operating our
                      service (AWS, Stripe, Supabase)
                    </li>
                    <li>When required by law or to protect our rights</li>
                    <li>
                      In connection with a business transfer or acquisition
                    </li>
                  </ul>
                </CardContent>
              </Card>

              {/* Your Rights */}
              <Card>
                <CardHeader>
                  <CardTitle>Your Privacy Rights</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    You have the right to:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>Access your personal information</li>
                    <li>Correct inaccurate or incomplete data</li>
                    <li>Delete your account and associated data</li>
                    <li>Export your data in a portable format</li>
                    <li>Opt out of marketing communications</li>
                    <li>Withdraw consent for data processing</li>
                  </ul>
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <p className="text-sm">
                      To exercise these rights, please contact us at{" "}
                      <a
                        href="mailto:jonathan@pianofi.ca"
                        className="text-primary hover:underline"
                      >
                        jonathan@pianofi.ca
                      </a>{" "}
                      or{" "}
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

              {/* Cookies */}
              <Card>
                <CardHeader>
                  <CardTitle>Cookies and Tracking</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    We use cookies and similar technologies to enhance your
                    experience:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>Essential cookies for service functionality</li>
                    <li>Analytics cookies to understand usage patterns</li>
                    <li>Preference cookies to remember your settings</li>
                  </ul>
                  <p className="text-muted-foreground">
                    You can control cookie preferences through your browser
                    settings.
                  </p>
                </CardContent>
              </Card>

              {/* Changes to Policy */}
              <Card>
                <CardHeader>
                  <CardTitle>Changes to This Policy</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    We may update this Privacy Policy from time to time. We will
                    notify you of any changes by:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>Posting the new policy on this page</li>
                    <li>Updating the "Last updated" date</li>
                    <li>
                      Sending you an email notification for significant changes
                    </li>
                  </ul>
                </CardContent>
              </Card>

              {/* Contact */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5 text-primary" />
                    Contact Us
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">
                    If you have any questions about this Privacy Policy or our
                    data practices, please contact us:
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
            <a href="#" className="text-xs hover:underline underline-offset-4">
              Terms of Service
            </a>
            <a
              href="/privacy"
              className="text-xs hover:underline underline-offset-4"
            >
              Privacy Policy
            </a>
            <a href="#" className="text-xs hover:underline underline-offset-4">
              Contact
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}
