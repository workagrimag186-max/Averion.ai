"use client";

import {
  Building2,
  CheckCircle2,
  ChevronDown,
  Globe2,
  LoaderCircle,
  Lock,
  LogOut,
  Mail,
  Pencil,
  Send,
  ShieldCheck,
  Trash2,
  UserRound,
  Users,
  XCircle
} from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

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

type Status = {
  kind: "success" | "error";
  message: string;
} | null;

function displayValue(value: string | null | undefined) {
  return value?.trim() || "Not set";
}

function displayName(member: TeamMember) {
  return member.name?.trim() || member.email;
}

function initials(value: string | null | undefined) {
  const parts = value?.trim().split(/\s+/).filter(Boolean) ?? [];
  if (!parts.length) return "A";
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export function AccountSummary() {
  const router = useRouter();
  const supabase = useMemo(() => getSupabaseBrowserClient(), []);
  const [activeTab, setActiveTab] = useState<"profile" | "team">("profile");
  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [invitations, setInvitations] = useState<OrganizationInvitation[]>([]);
  const [name, setName] = useState("");
  const [jobTitle, setJobTitle] = useState("");
  const [language, setLanguage] = useState("en");
  const [organizationName, setOrganizationName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [roleFilter, setRoleFilter] = useState<"all" | "owner" | "member">(
    "all"
  );
  const [status, setStatus] = useState<Status>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingOrganization, setIsSavingOrganization] = useState(false);
  const [isInviting, setIsInviting] = useState(false);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [updatingRoleId, setUpdatingRoleId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [isSigningOut, setIsSigningOut] = useState(false);

  const isOwner = profile?.role === "owner";
  const members = useMemo(
    () =>
      (team?.members ?? []).filter(
        (member) => roleFilter === "all" || member.role === roleFilter
      ),
    [roleFilter, team]
  );

  async function refreshWorkspace() {
    const [nextProfile, nextTeam, nextInvitations] = await Promise.all([
      getAccountProfile(),
      getTeamInfo(),
      listOrganizationInvitations()
    ]);
    setProfile(nextProfile);
    setTeam(nextTeam);
    setInvitations(nextInvitations);
    setName(nextProfile.name ?? "");
    setJobTitle(nextProfile.job_title ?? "");
    setLanguage(nextProfile.language_preference ?? "en");
    setOrganizationName(nextTeam.organization_name);
  }

  useEffect(() => {
    let active = true;

    async function loadInitialWorkspace() {
      try {
        const [nextProfile, nextTeam, nextInvitations] = await Promise.all([
          getAccountProfile(),
          getTeamInfo(),
          listOrganizationInvitations()
        ]);
        if (!active) return;
        setProfile(nextProfile);
        setTeam(nextTeam);
        setInvitations(nextInvitations);
        setName(nextProfile.name ?? "");
        setJobTitle(nextProfile.job_title ?? "");
        setLanguage(nextProfile.language_preference ?? "en");
        setOrganizationName(nextTeam.organization_name);
      } catch (error) {
        if (active) {
          setStatus({
            kind: "error",
            message:
              error instanceof Error
                ? error.message
              : "Could not load account and workspace."
          });
        }
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void loadInitialWorkspace();
    return () => {
      active = false;
    };
  }, []);

  async function handleProfileSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSavingProfile(true);
    setStatus(null);
    try {
      const updated = await updateAccountProfile({
        name: name.trim() || null,
        job_title: jobTitle.trim() || null,
        language_preference: language
      });
      setProfile(updated);
      setStatus({ kind: "success", message: "Profile changes saved." });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not save profile."
      });
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handleOrganizationSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!organizationName.trim()) return;
    setIsSavingOrganization(true);
    setStatus(null);
    try {
      const updated = await updateOrganizationName(organizationName.trim());
      setTeam(updated);
      setProfile((current) =>
        current
          ? { ...current, organization_name: updated.organization_name }
          : current
      );
      setStatus({ kind: "success", message: "Organization name updated." });
    } catch (error) {
      setStatus({
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

  async function handleInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsInviting(true);
    setStatus(null);
    try {
      const invitation = await createOrganizationInvitation(inviteEmail.trim());
      setInviteEmail("");
      setStatus({
        kind: "success",
        message: `Invitation created for ${invitation.invited_email}.`
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not send invitation."
      });
    } finally {
      setIsInviting(false);
    }
  }

  async function handleAccept(invitation: OrganizationInvitation) {
    setAcceptingId(invitation.invitation_id);
    setStatus(null);
    try {
      await acceptOrganizationInvitation(invitation.invitation_id);
      await refreshWorkspace();
      setStatus({
        kind: "success",
        message: `You joined ${invitation.organization_name}.`
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Could not accept invitation."
      });
    } finally {
      setAcceptingId(null);
    }
  }

  async function handleRole(member: TeamMember, role: TeamMember["role"]) {
    setUpdatingRoleId(member.user_id);
    setStatus(null);
    try {
      const updated = await updateTeamMemberRole(member.user_id, role);
      setTeam((current) =>
        current
          ? {
              ...current,
              members: current.members.map((item) =>
                item.user_id === updated.user_id ? updated : item
              )
            }
          : current
      );
      setStatus({
        kind: "success",
        message: `${displayName(updated)} is now an ${updated.role}.`
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not change role."
      });
    } finally {
      setUpdatingRoleId(null);
    }
  }

  async function handleRemove(member: TeamMember) {
    if (
      !window.confirm(
        `Remove ${displayName(member)} from this organization? They will receive a private workspace where they become owner.`
      )
    ) {
      return;
    }
    setRemovingId(member.user_id);
    setStatus(null);
    try {
      await removeTeamMember(member.user_id);
      setTeam((current) =>
        current
          ? {
              ...current,
              members: current.members.filter(
                (item) => item.user_id !== member.user_id
              )
            }
          : current
      );
      setStatus({
        kind: "success",
        message: `${displayName(member)} was moved to a private workspace.`
      });
    } catch (error) {
      setStatus({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Could not remove member."
      });
    } finally {
      setRemovingId(null);
    }
  }

  async function handleLogout() {
    setIsSigningOut(true);
    if (supabase) await supabase.auth.signOut();
    router.replace("/login");
  }

  if (isLoading) {
    return (
      <div className="mx-auto flex min-h-[520px] max-w-[1400px] items-center justify-center text-sm text-zinc-500">
        <LoaderCircle className="mr-2 animate-spin" size={18} />
        Loading account and workspace
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-[1400px]">
      <div>
        <p className="text-xs font-semibold uppercase text-blue-400">
          Workspace settings
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-white">
          Account &amp; Workspace
        </h1>
        <p className="mt-2 text-sm text-zinc-400">
          Manage your profile, language preference, organization, and team.
        </p>
      </div>

      <div className="mt-8 flex gap-7 border-b border-white/[0.08]">
        <button
          className={`border-b-2 px-1 pb-4 text-sm font-semibold transition ${
            activeTab === "profile"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-500 hover:text-white"
          }`}
          onClick={() => setActiveTab("profile")}
          type="button"
        >
          My Profile
        </button>
        <button
          className={`border-b-2 px-1 pb-4 text-sm font-semibold transition ${
            activeTab === "team"
              ? "border-blue-500 text-blue-400"
              : "border-transparent text-zinc-500 hover:text-white"
          }`}
          onClick={() => setActiveTab("team")}
          type="button"
        >
          Organization &amp; Team
        </button>
      </div>

      {status && (
        <div
          className={`mt-5 flex items-start gap-3 rounded-md border px-4 py-3 text-sm ${
            status.kind === "success"
              ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
              : "border-red-500/30 bg-red-500/10 text-red-200"
          }`}
          role={status.kind === "error" ? "alert" : "status"}
        >
          {status.kind === "success" ? (
            <CheckCircle2 size={18} />
          ) : (
            <XCircle size={18} />
          )}
          <span>{status.message}</span>
        </div>
      )}

      {activeTab === "profile" ? (
        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
          <section className="rounded-md border border-white/[0.08] bg-[#1a1a1a] p-5 sm:p-8">
            <div className="flex items-center gap-5 border-b border-white/[0.08] pb-7">
              {profile?.avatar_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  alt=""
                  className="size-20 rounded-md object-cover"
                  src={profile.avatar_url}
                />
              ) : (
                <div className="flex size-20 items-center justify-center rounded-md bg-blue-500 text-2xl font-semibold text-white">
                  {initials(profile?.name ?? profile?.email)}
                </div>
              )}
              <div className="min-w-0">
                <h2 className="truncate text-xl font-semibold text-white">
                  {displayValue(profile?.name)}
                </h2>
                <p className="mt-1 truncate text-sm text-zinc-500">
                  {displayValue(profile?.job_title)}
                </p>
              </div>
            </div>

            <form
              className="mt-7 grid gap-5"
              onSubmit={handleProfileSave}
            >
              <div className="grid gap-5 md:grid-cols-2">
                <label className="grid gap-2">
                  <span className="text-xs font-semibold text-zinc-400">
                    Display name
                  </span>
                  <input
                    className="h-11 rounded-md border border-white/10 bg-[#0d0d0d] px-3 text-sm text-white outline-none focus:border-blue-500/60"
                    maxLength={120}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Add your name"
                    value={name}
                  />
                </label>
                <label className="grid gap-2">
                  <span className="text-xs font-semibold text-zinc-400">
                    Job title
                  </span>
                  <input
                    className="h-11 rounded-md border border-white/10 bg-[#0d0d0d] px-3 text-sm text-white outline-none focus:border-blue-500/60"
                    maxLength={120}
                    onChange={(event) => setJobTitle(event.target.value)}
                    placeholder="Knowledge manager, founder, engineer..."
                    value={jobTitle}
                  />
                </label>
              </div>

              <label className="grid gap-2">
                <span className="text-xs font-semibold text-zinc-400">
                  Email address
                </span>
                <span className="flex h-11 items-center justify-between rounded-md border border-white/[0.06] bg-[#141414] px-3 text-sm text-zinc-500">
                  {displayValue(profile?.email)}
                  <Lock size={15} />
                </span>
              </label>

              <label className="grid gap-2">
                <span className="text-xs font-semibold text-zinc-400">
                  Preferred language
                </span>
                <span className="relative">
                  <Globe2
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600"
                    size={16}
                  />
                  <select
                    className="h-11 w-full appearance-none rounded-md border border-white/10 bg-[#0d0d0d] pl-10 pr-9 text-sm text-white outline-none focus:border-blue-500/60"
                    onChange={(event) => setLanguage(event.target.value)}
                    value={language}
                  >
                    <option value="en">English</option>
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="es">Spanish (Español)</option>
                    <option value="fr">French (Français)</option>
                    <option value="de">German (Deutsch)</option>
                    <option value="ja">Japanese (日本語)</option>
                  </select>
                  <ChevronDown
                    className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-600"
                    size={16}
                  />
                </span>
                <span className="text-xs leading-5 text-zinc-600">
                  This controls the chatbot&apos;s response language and your saved
                  preference.
                </span>
              </label>

              <div className="flex justify-end border-t border-white/[0.08] pt-6">
                <button
                  className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-blue-500 px-6 text-sm font-semibold text-white transition hover:bg-blue-600 disabled:opacity-50"
                  disabled={isSavingProfile}
                  type="submit"
                >
                  {isSavingProfile && (
                    <LoaderCircle className="animate-spin" size={16} />
                  )}
                  {isSavingProfile ? "Saving..." : "Save changes"}
                </button>
              </div>
            </form>
          </section>

          <aside className="space-y-5">
            <section className="rounded-md border border-white/[0.08] bg-[#1a1a1a] p-5">
              <h2 className="text-xs font-semibold uppercase text-zinc-500">
                Account summary
              </h2>
              <dl className="mt-5 space-y-5">
                <div>
                  <dt className="text-[11px] text-zinc-600">Email</dt>
                  <dd className="mt-1 break-words text-sm text-zinc-200">
                    {displayValue(profile?.email)}
                  </dd>
                </div>
                <div>
                  <dt className="text-[11px] text-zinc-600">Organization</dt>
                  <dd className="mt-1 text-sm text-zinc-200">
                    {displayValue(profile?.organization_name)}
                  </dd>
                </div>
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <dt className="text-[11px] text-zinc-600">Role</dt>
                    <dd className="mt-1 text-sm capitalize text-zinc-200">
                      {displayValue(profile?.role)}
                    </dd>
                  </div>
                  <span className="rounded-md border border-cyan-500/30 bg-cyan-500/10 px-2 py-1 text-[10px] font-semibold uppercase text-cyan-400">
                    {profile?.role ?? "member"}
                  </span>
                </div>
                <div className="border-t border-white/[0.08] pt-4">
                  <dt className="text-[11px] text-zinc-600">User ID</dt>
                  <dd className="mt-2 break-all rounded-md bg-[#0d0d0d] p-2 font-mono text-[10px] text-zinc-500">
                    {displayValue(profile?.user_id)}
                  </dd>
                </div>
                <div className="flex items-center gap-2 text-xs text-zinc-500">
                  <ShieldCheck className="text-cyan-400" size={16} />
                  Authenticated with Supabase
                </div>
              </dl>
              <button
                className="mt-6 inline-flex h-10 w-full items-center justify-center gap-2 rounded-md border border-red-500/30 text-sm font-semibold text-red-300 hover:bg-red-500/10 disabled:opacity-50"
                disabled={isSigningOut}
                onClick={() => void handleLogout()}
                type="button"
              >
                <LogOut size={16} />
                {isSigningOut ? "Signing out..." : "Sign out"}
              </button>
            </section>
          </aside>
        </div>
      ) : (
        <div className="mt-8 space-y-6">
          <section className="rounded-md border border-white/[0.08] bg-[#1a1a1a] p-5 sm:p-7">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex min-w-0 items-center gap-4">
                <span className="flex size-14 shrink-0 items-center justify-center rounded-md border border-white/10 bg-zinc-800 text-zinc-300">
                  <Building2 size={26} />
                </span>
                <div className="min-w-0">
                  <h2 className="truncate text-xl font-semibold text-white">
                    {displayValue(team?.organization_name)}
                  </h2>
                  <p className="mt-2 flex items-center gap-2 text-xs text-zinc-500">
                    <Users className="text-cyan-400" size={15} />
                    {team?.members.length ?? 0} members
                    <span className="rounded-md border border-blue-500/25 bg-blue-500/10 px-2 py-0.5 text-[10px] font-semibold uppercase text-blue-400">
                      {profile?.role}
                    </span>
                  </p>
                </div>
              </div>
              {isOwner && (
                <form
                  className="flex min-w-0 flex-1 gap-2 lg:max-w-xl"
                  onSubmit={handleOrganizationSave}
                >
                  <label className="relative min-w-0 flex-1">
                    <Pencil
                      className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600"
                      size={15}
                    />
                    <input
                      aria-label="Organization name"
                      className="h-10 w-full rounded-md border border-white/10 bg-[#0d0d0d] pl-9 pr-3 text-sm text-white outline-none focus:border-blue-500/60"
                      maxLength={120}
                      onChange={(event) =>
                        setOrganizationName(event.target.value)
                      }
                      value={organizationName}
                    />
                  </label>
                  <button
                    className="h-10 rounded-md bg-blue-500 px-4 text-sm font-semibold text-white hover:bg-blue-600 disabled:opacity-50"
                    disabled={
                      isSavingOrganization || !organizationName.trim()
                    }
                    type="submit"
                  >
                    {isSavingOrganization ? "Saving..." : "Save"}
                  </button>
                </form>
              )}
            </div>
          </section>

          <div className="grid gap-6 xl:grid-cols-[330px_minmax(0,1fr)]">
            <div className="space-y-6">
              <section className="rounded-md border border-white/[0.08] bg-[#1a1a1a] p-5">
                <h2 className="flex items-center gap-2 font-semibold text-white">
                  <Mail className="text-blue-400" size={18} />
                  {isOwner ? "Invite members" : "Workspace invitations"}
                </h2>
                {isOwner && (
                  <form className="mt-5" onSubmit={handleInvite}>
                    <label className="text-[11px] font-semibold uppercase text-zinc-500">
                      Email address
                    </label>
                    <div className="mt-2 flex gap-2">
                      <input
                        className="h-10 min-w-0 flex-1 rounded-md border border-white/10 bg-[#0d0d0d] px-3 text-sm text-white outline-none focus:border-blue-500/60"
                        maxLength={254}
                        onChange={(event) => setInviteEmail(event.target.value)}
                        placeholder="colleague@example.com"
                        type="email"
                        value={inviteEmail}
                      />
                      <button
                        aria-label="Send invitation"
                        className="flex size-10 items-center justify-center rounded-md bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50"
                        disabled={isInviting || !inviteEmail.trim()}
                        type="submit"
                      >
                        {isInviting ? (
                          <LoaderCircle className="animate-spin" size={16} />
                        ) : (
                          <Send size={16} />
                        )}
                      </button>
                    </div>
                    <p className="mt-3 text-xs leading-5 text-zinc-600">
                      The invited user can accept after signing in with the same
                      email address.
                    </p>
                  </form>
                )}

                <div
                  className={`${
                    isOwner
                      ? "mt-6 border-t border-white/[0.08] pt-5"
                      : "mt-5"
                  }`}
                >
                  <h3 className="text-[11px] font-semibold uppercase text-zinc-500">
                    Invitations for you
                  </h3>
                  {invitations.length ? (
                    <div className="mt-3 space-y-2">
                      {invitations.map((invitation) => (
                        <div
                          className="rounded-md border border-white/[0.08] bg-[#141414] p-3"
                          key={invitation.invitation_id}
                        >
                          <p className="text-sm font-semibold text-zinc-200">
                            {invitation.organization_name}
                          </p>
                          <p className="mt-1 text-xs text-zinc-600">
                            Sent to {invitation.invited_email}
                          </p>
                          <button
                            className="mt-3 h-8 w-full rounded-md border border-blue-500/30 bg-blue-500/10 text-xs font-semibold text-blue-400 hover:bg-blue-500/15 disabled:opacity-50"
                            disabled={acceptingId === invitation.invitation_id}
                            onClick={() => void handleAccept(invitation)}
                            type="button"
                          >
                            {acceptingId === invitation.invitation_id
                              ? "Accepting..."
                              : "Accept invitation"}
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-3 text-xs leading-5 text-zinc-600">
                      No pending invitations for your email.
                    </p>
                  )}
                </div>
              </section>

              <section className="rounded-md border border-white/[0.08] bg-[#1a1a1a] p-5">
                <h2 className="flex items-center gap-2 text-sm font-semibold text-white">
                  <ShieldCheck className="text-cyan-400" size={18} />
                  Access rules
                </h2>
                <ul className="mt-4 space-y-3 text-xs leading-5 text-zinc-500">
                  <li>All members can upload and chat with organization documents.</li>
                  <li>Only owners can delete documents or manage team access.</li>
                  <li>Owners can promote or demote other owners and members.</li>
                </ul>
              </section>
            </div>

            <section className="overflow-hidden rounded-md border border-white/[0.08] bg-[#1a1a1a]">
              <div className="flex flex-col gap-3 border-b border-white/[0.08] p-5 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="flex items-center gap-2 font-semibold text-white">
                    <Users className="text-cyan-400" size={18} />
                    Active members
                  </h2>
                  <p className="mt-1 text-xs text-zinc-600">
                    {members.length} shown
                  </p>
                </div>
                <label className="relative">
                  <select
                    aria-label="Filter members by role"
                    className="h-9 appearance-none rounded-md border border-white/10 bg-[#0d0d0d] pl-3 pr-8 text-xs text-zinc-300 outline-none"
                    onChange={(event) =>
                      setRoleFilter(
                        event.target.value as "all" | "owner" | "member"
                      )
                    }
                    value={roleFilter}
                  >
                    <option value="all">All roles</option>
                    <option value="owner">Owners</option>
                    <option value="member">Members</option>
                  </select>
                  <ChevronDown
                    className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-zinc-600"
                    size={14}
                  />
                </label>
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-[#131313] text-[10px] uppercase text-zinc-600">
                    <tr>
                      <th className="px-5 py-3">Member</th>
                      <th className="px-5 py-3">Job title</th>
                      <th className="px-5 py-3">Role</th>
                      <th className="px-5 py-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.06]">
                    {members.map((member) => {
                      const isSelf = member.user_id === profile?.user_id;
                      const canManage = isOwner && !isSelf;
                      return (
                        <tr key={member.user_id}>
                          <td className="px-5 py-4">
                            <div className="flex items-center gap-3">
                              <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-zinc-800 text-xs font-semibold text-zinc-300">
                                {initials(member.name ?? member.email)}
                              </span>
                              <span className="min-w-0">
                                <span className="block truncate font-semibold text-zinc-200">
                                  {displayName(member)}
                                  {isSelf && (
                                    <span className="ml-2 text-[10px] text-blue-400">
                                      You
                                    </span>
                                  )}
                                </span>
                                <span className="mt-1 block truncate text-xs text-zinc-600">
                                  {member.email}
                                </span>
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-4 text-zinc-500">
                            {displayValue(member.job_title)}
                          </td>
                          <td className="px-5 py-4">
                            {canManage ? (
                              <select
                                className="h-9 rounded-md border border-white/10 bg-[#0d0d0d] px-3 text-xs capitalize text-zinc-200 outline-none focus:border-blue-500/60 disabled:opacity-50"
                                disabled={updatingRoleId === member.user_id}
                                onChange={(event) =>
                                  void handleRole(
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
                              <span className="rounded-md border border-white/10 bg-zinc-900 px-2 py-1 text-[10px] font-semibold uppercase text-zinc-400">
                                {member.role}
                              </span>
                            )}
                          </td>
                          <td className="px-5 py-4 text-right">
                            {canManage ? (
                              <button
                                aria-label={`Remove ${displayName(member)}`}
                                className="rounded-md p-2 text-zinc-600 hover:bg-red-500/10 hover:text-red-400 disabled:opacity-50"
                                disabled={removingId === member.user_id}
                                onClick={() => void handleRemove(member)}
                                title="Remove member"
                                type="button"
                              >
                                {removingId === member.user_id ? (
                                  <LoaderCircle
                                    className="animate-spin"
                                    size={16}
                                  />
                                ) : (
                                  <Trash2 size={16} />
                                )}
                              </button>
                            ) : (
                              <UserRound className="ml-auto text-zinc-700" size={16} />
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
