AfyaLink: Health Triage & Case Management Platform

AfyaLink is a robust health triage and case management platform designed to bridge the gap between patients and community health agents via accessible technology. The platform facilitates the entire lifecycle of a health inquiry, from initial symptom reporting via USSD to agent assignment, follow-up, and payment processing.

This project provides a complete, end-to-end workflow for both patients and agents, establishing a solid and scalable foundation for future enhancements.

🎥 Video Demonstration

Click the image below to watch a full demonstration of the AfyaLink platform's core features, from agent registration and approval to patient case submission and management.

Direct Link: https://drive.google.com/file/d/1G7R3KJYFWIffXdDNuxXMu0Vw0XFBHJTS/view?usp=drive_link


✨ Core Features

The Patient Experience

    Passwordless Web Portal Login: Patients can securely log in to their personal dashboard using their phone number and a One-Time Password (OTP).

    Personal Dashboard: A clean, well-arranged dashboard where patients can:

        View the real-time status of all their submitted cases.

        Read notes and updates left by their assigned agent.

        See a clear notification when a payment has been requested.

    Web-Based Case Submission: Patients can submit new health concerns directly through a simple form on their dashboard, in addition to the USSD service.

The Agent Experience

    Secure Self-Registration & Approval: A comprehensive registration form with live validation allows new agents to sign up. Accounts remain inactive and are held in a "pending" state until an administrator reviews and approves them.

    Comprehensive Dashboard: After logging in, agents are presented with a powerful dashboard to:

        View a list of all cases in the system.

        Filter to see only their assigned cases.

        Sort cases by urgency, date, or status.

        Claim unassigned cases with a single click.

    Case Management: Agents can drill down into a case's details, add their own notes for the patient, update the case status, and trigger M-Pesa payment requests.

System & Administrative Features

    USSD-Based Case Creation: A simple and accessible USSD menu allows any user to report health symptoms, which automatically creates a case in the system.

    Automated Case Assignment: New cases are automatically assigned to the least busy, active agent, ensuring a balanced workload and prompt responses.

    Integrated Payment System: The platform is integrated with the Safaricom Daraja API (in the sandbox environment) to allow agents to initiate M-Pesa STK Push payment requests directly to patients.

🛠️ Technologies Used

    Backend: Django & Django REST Framework

    Authentication: JWT (JSON Web Tokens) & OTP

    Frontend: Single-Page Application using HTML, Tailwind CSS, and Vanilla JavaScript

    Database: MySQL (deployed on PythonAnywhere)

    APIs: Safaricom Daraja (M-Pesa), structured for Africa's Talking (USSD/SMS)

🚀 Future Development Roadmap

The following phases outline the plan to evolve AfyaLink into an intelligent, proactive health monitoring and support system.

    Phase 1: Enhanced User Dashboard & Payment Integration (Payment History, Case Timeline)

    Phase 2: AI-Powered Triage and Agent Co-Pilot (Urgency, Category, and Summary generation)

    Phase 3: Proactive Patient Engagement & Follow-up (AI-powered SMS questions, personalized alerts)

    Phase 4: Chronic Disease Management & Advanced Monitoring (Automated check-ins, medication reminders)
