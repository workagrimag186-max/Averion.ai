"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AccountProfile,
  OrganizationInvitation,
  TeamInfo,
  TeamMember,
  acceptOrganizationInvitation,
  createOrganizationInvitation,
  getAccountProfile,
  getTeamInfo,
  listOrganizationInvitations,
  removeTeamMember,
  updateAccountProfile,
  updateOrganizationName,
  updateTeamMemberRole
} from "@/lib/api";
import { getSupabaseBrowserClient } from "@/lib/supabase";

type FormStatus = {
  kind: "idle" | "success" | "error";
  message: string;
};

function displayValue(value: string | null | undefined): string {
  return value?.trim() || "Not set";
}

function formatRole(role: string | null): string {
  if (!role) {
    return "Not assigned";
  }

  return role.charAt(0).toUpperCase() + role.slice(1);
}

function memberDisplayName(member: TeamMember): string {
  return member.name?.trim() || member.email;
}

export function AccountSummary() {
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [name, setName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [languagePreference, setLanguagePreference] = useState("en");
  const [organizationName, setOrganizationName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingOrganization, setIsSavingOrganization] = useState(false);
  const [isSendingInvite, setIsSendingInvite] = useState(false);
  const [acceptingInvitationId, setAcceptingInvitationId] = useState<
    string | null
  >(null);
  const [removingUserId, setRemovingUserId] = useState<string | null>(null);
  const [updatingRoleUserId, setUpdatingRoleUserId] = useState<string | null>(
    null
  );
  const [isSigningOut, setIsSigningOut] = useState(false);
  const [status, setStatus] = useState<FormStatus>({
    kind: "idle",
    message: ""
  });
  const [teamStatus, setTeamStatus] = useState<FormStatus>({
    kind: "idle",
    message: ""
  });
  const isOwner = profile?.role === "owner";

  useEffect(() => {
    let ignore = false;

    async function loadProfile() {
      setIsLoading(true);
      setStatus({ kind: "idle", message: "" });

      try {
        const [nextProfile, nextTeam] = await Promise.all([
          getAccountProfile(),
          getTeamInfo()
        ]);
        const nextInvitations = await listOrganizationInvitations();

        if (ignore) {
          return;
        }

        setProfile(nextProfile);
        setTeam(nextTeam);
        setInvitations(nextInvitations);
        setName(nextProfile.name ?? "");
        setJobTitle(nextProfile.job_title ?? "");
        setLanguagePreference(nextProfile.language_preference ?? "en");
        setOrganizationName(nextTeam.organization_name);
      } catch (error) {
        if (ignore) {
          return;
        }

        setStatus({
          kind: "error",
          message:
            error instanceof Error
              ? error.message
              : "Could not load account profile."
        });
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    void loadProfile();

    return () => {
      ignore = true;
    };
  }, []);

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSaving(true);
    setStatus({ kind: "idle", message: "" });

    try {
      const updatedProfile = await updateAccountProfile({
        name: name.trim() || null,
        job_title: jobTitle.trim() || null,
        language_preference: languagePreference
      });

      setProfile(updatedProfile);
      setName(updatedProfile.name ?? "");
      setJobTitle(updatedProfile.job_title ?? "");
      setLanguagePreference(updatedProfile.language_preference ?? "en");
      setStatus({
        kind: "success",
        message: "Profile updated."
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not update account profile."
      });
    } finally {
      setIsSaving(false);
    }
  }

  async function handleOrganizationSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSavingOrganization(true);
    setTeamStatus({ kind: "idle", message: "" });

    try {
      const updatedTeam = await updateOrganizationName(organizationName.trim());

      setTeam(updatedTeam);
      setOrganizationName(updatedTeam.organization_name);
      setProfile((currentProfile) =>
        currentProfile
          ? {
              ...currentProfile,
              organization_name: updatedTeam.organization_name
            }
          : currentProfile
      );
      setTeamStatus({
        kind: "success",
        message: "Organization updated."
      });
    } catch (error) {
      setTeamStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not update organization."
      });
    } finally {
      setIsSavingOrganization(false);
    }
  }

  async function handleRoleChange(
    member: TeamMember,
    role: TeamMember["role"]
  ) {
    setUpdatingRoleUserId(member.user_id);
    setTeamStatus({ kind: "idle", message: "" });

    try {
      const updatedMember = await updateTeamMemberRole(member.user_id, role);

      setTeam((currentTeam) =>
        currentTeam
          ? {
              ...currentTeam,
              members: currentTeam.members.map((currentMember) =>
                currentMember.user_id === updatedMember.user_id
                  ? updatedMember
                  : currentMember
              )
            }
          : currentTeam
      );
      setTeamStatus({
        kind: "success",
        message: `${memberDisplayName(updatedMember)} is now ${formatRole(
          updatedMember.role
        )}.`
      });
    } catch (error) {
      setTeamStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not update team member role."
      });
    } finally {
      setUpdatingRoleUserId(null);
    }
  }

  async function refreshWorkspace() {
    const [nextProfile, nextTeam, nextInvitations] = await Promise.all([
      getAccountProfile(),
      getTeamInfo(),
      listOrganizationInvitations()
    ]);

    setProfile(nextProfile);
    setTeam(nextTeam);
    setInvitations(nextInvitations);
    setOrganizationName(nextTeam.organization_name);
  }

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setIsSendingInvite(true);
    setTeamStatus({ kind: "idle", message: "" });

    try {
      const invitation = await createOrganizationInvitation(inviteEmail);

      setInviteEmail("");
      setTeamStatus({
        kind: "success",
        message: `Invite created for ${invitation.invited_email}.`
      });
    } catch (error) {
      setTeamStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not create invitation."
      });
    } finally {
      setIsSendingInvite(false);
    }
  }

  async function handleAcceptInvitation(invitationId: string) {
    setAcceptingInvitationId(invitationId);
    setTeamStatus({ kind: "idle", message: "" });

    try {
      await acceptOrganizationInvitation(invitationId);
      await refreshWorkspace();
      setTeamStatus({
        kind: "success",
        message: "Invitation accepted."
      });
    } catch (error) {
      setTeamStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not accept invitation."
      });
    } finally {
      setAcceptingInvitationId(null);
    }
  }

  async function handleRemoveMember(member: TeamMember) {
    setRemovingUserId(member.user_id);
    setTeamStatus({ kind: "idle", message: "" });

    try {
      await removeTeamMember(member.user_id);
      setTeam((currentTeam) =>
        currentTeam
          ? {
              ...currentTeam,
              members: currentTeam.members.filter(
                (currentMember) => currentMember.user_id !== member.user_id
              )
            }
          : currentTeam
      );
      setTeamStatus({
        kind: "success",
        message: `${memberDisplayName(member)} was moved to a private workspace.`
      });
    } catch (error) {
      setTeamStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not remove team member."
      });
    } finally {
      setRemovingUserId(null);
    }
  }

  async function handleLogout() {
    if (!supabase) {
      router.replace("/login");
      return;
    }

    setIsSigningOut(true);
    await supabase.auth.signOut();
    router.replace("/login");
  }

  if (isLoading) {
    return (
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium text-blue-700">Loading profile</p>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <div className="h-24 rounded-lg bg-slate-100" />
          <div className="h-24 rounded-lg bg-slate-100" />
          <div className="h-44 rounded-lg bg-slate-100 md:col-span-2" />
        </div>
      </section>
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr]">
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-700">Account details</p>
            <h2 className="mt-1 text-xl font-semibold tracking-normal text-slate-950">
              Profile
            </h2>
          </div>
          <button
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSigningOut}
            onClick={handleLogout}
            type="button"
          >
            {isSigningOut ? "Signing out..." : "Logout"}
          </button>
        </div>

        {status.message && (
          <div
            className={`mt-5 rounded-md border px-4 py-3 text-sm ${
              status.kind === "success"
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-800"
            }`}
          >
            {status.message}
          </div>
        )}

        <form className="mt-6 grid gap-5" onSubmit={handleSave}>
          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Display name
            </span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
              placeholder="Add your name"
              type="text"
              value={name}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Job title
            </span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              maxLength={120}
              onChange={(event) => setJobTitle(event.target.value)}
              placeholder="Knowledge manager, founder, engineer..."
              type="text"
              value={jobTitle}
            />
          </label>

          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Language
            </span>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              onChange={(event) => setLanguagePreference(event.target.value)}
              value={languagePreference}
            >
              <option value="en">English</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="es">Spanish (Español)</option>
              <option value="fr">French (Français)</option>
              <option value="de">German (Deutsch)</option>
              <option value="ja">Japanese (日本語)</option>
            </select>
            <p className="text-xs text-slate-500">
              Select your preferred language for the interface and chatbot
            </p>
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <button
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSaving}
              type="submit"
            >
              {isSaving ? "Saving..." : "Save profile"}
            </button>
            <p className="text-sm text-slate-500">
              Email stays read-only for the MVP.
            </p>
          </div>
        </form>
      </section>

      <aside className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-950">Workspace access</h2>
        <dl className="mt-5 grid gap-4">
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Email
            </dt>
            <dd className="mt-2 break-words text-sm font-medium text-slate-950">
              {displayValue(profile?.email)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Organization
            </dt>
            <dd className="mt-2 text-sm font-medium text-slate-950">
              {displayValue(profile?.organization_name)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Role
            </dt>
            <dd className="mt-2 text-sm font-medium text-slate-950">
              {formatRole(profile?.role ?? null)}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              User ID
            </dt>
            <dd className="mt-2 break-all font-mono text-xs text-slate-600">
              {displayValue(profile?.user_id)}
            </dd>
          </div>
        </dl>
      </aside>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm lg:col-span-2">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-700">
              Organization settings
            </p>
            <h2 className="mt-1 text-xl font-semibold tracking-normal text-slate-950">
              Team access
            </h2>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
            {team?.members.length ?? 0} members
          </span>
        </div>

        {teamStatus.message && (
          <div
            className={`mt-5 rounded-md border px-4 py-3 text-sm ${
              teamStatus.kind === "success"
                ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                : "border-red-200 bg-red-50 text-red-800"
            }`}
          >
            {teamStatus.message}
          </div>
        )}

        <form
          className="mt-6 grid gap-3 sm:grid-cols-[1fr_auto]"
          onSubmit={handleOrganizationSave}
        >
          <label className="grid gap-2">
            <span className="text-sm font-semibold text-slate-700">
              Organization name
            </span>
            <input
              className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-50 disabled:text-slate-500"
              disabled={!isOwner || isSavingOrganization}
              maxLength={120}
              onChange={(event) => setOrganizationName(event.target.value)}
              type="text"
              value={organizationName}
            />
          </label>
          <div className="flex items-end">
            <button
              className="w-full rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              disabled={!isOwner || isSavingOrganization}
              type="submit"
            >
              {isSavingOrganization ? "Saving..." : "Save organization"}
            </button>
          </div>
        </form>

        {isOwner && (
          <form
            className="mt-6 grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 sm:grid-cols-[1fr_auto]"
            onSubmit={handleInvite}
          >
            <label className="grid gap-2">
              <span className="text-sm font-semibold text-slate-700">
                Invite by email
              </span>
              <input
                className="rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                maxLength={254}
                onChange={(event) => setInviteEmail(event.target.value)}
                placeholder="teammate@example.com"
                type="email"
                value={inviteEmail}
              />
            </label>
            <div className="flex items-end">
              <button
                className="w-full rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                disabled={isSendingInvite || !inviteEmail.trim()}
                type="submit"
              >
                {isSendingInvite ? "Sending..." : "Send invite"}
              </button>
            </div>
          </form>
        )}

        {invitations.length > 0 && (
          <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-4">
            <h3 className="text-sm font-semibold text-blue-950">
              Pending invitations
            </h3>
            <div className="mt-3 grid gap-3">
              {invitations.map((invitation) => (
                <div
                  className="flex flex-col gap-3 rounded-md border border-blue-100 bg-white p-3 sm:flex-row sm:items-center sm:justify-between"
                  key={invitation.invitation_id}
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-950">
                      {invitation.organization_name}
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      Invited as {invitation.invited_email}
                    </p>
                  </div>
                  <button
                    className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={
                      acceptingInvitationId === invitation.invitation_id
                    }
                    onClick={() =>
                      void handleAcceptInvitation(invitation.invitation_id)
                    }
                    type="button"
                  >
                    {acceptingInvitationId === invitation.invitation_id
                      ? "Accepting..."
                      : "Accept invite"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6 overflow-hidden rounded-lg border border-slate-200">
          <div className="hidden grid-cols-[minmax(0,1.4fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.6fr)] gap-4 bg-slate-50 px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 sm:grid">
            <span>Member</span>
            <span>Job title</span>
            <span>Role</span>
            <span>Actions</span>
          </div>

          {team?.members.map((member) => {
            const canChangeRole =
              isOwner && member.user_id !== profile?.user_id;

            return (
              <div
                className="grid gap-3 border-t border-slate-200 px-4 py-4 text-sm first:border-t-0 sm:grid-cols-[minmax(0,1.4fr)_minmax(0,0.7fr)_minmax(0,0.7fr)_minmax(0,0.6fr)] sm:gap-4 sm:first:border-t"
                key={member.user_id}
              >
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-950">
                    {memberDisplayName(member)}
                  </p>
                  <p className="mt-1 truncate text-slate-500">
                    {member.email}
                  </p>
                </div>
                <p className="self-center text-slate-600">
                  {displayValue(member.job_title)}
                </p>
                <div className="self-center">
                  {canChangeRole ? (
                    <select
                      className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={updatingRoleUserId === member.user_id}
                      onChange={(event) =>
                        void handleRoleChange(
                          member,
                          event.target.value as TeamMember["role"]
                        )
                      }
                      value={member.role}
                    >
                      <option value="member">Member</option>
                      <option value="owner">Owner</option>
                    </select>
                  ) : (
                    <span className="inline-flex rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                      {formatRole(member.role)}
                    </span>
                  )}
                </div>
                <div className="self-center">
                  {isOwner && member.user_id !== profile?.user_id ? (
                    <button
                      className="rounded-md border border-red-200 px-3 py-2 text-xs font-semibold text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={removingUserId === member.user_id}
                      onClick={() => void handleRemoveMember(member)}
                      type="button"
                    >
                      {removingUserId === member.user_id
                        ? "Removing..."
                        : "Remove"}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-400">-</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
