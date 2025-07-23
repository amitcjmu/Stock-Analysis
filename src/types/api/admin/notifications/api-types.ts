/**
 * Notification API Types
 * 
 * Request and response type definitions for notification management APIs.
 * 
 * Generated with CC for modular admin type organization.
 */

import type {
  BaseApiRequest,
  BaseApiResponse,
  MultiTenantContext,
  ListRequest,
  ListResponse,
  CreateRequest,
  CreateResponse
} from '../../shared';

import type { NotificationData, NotificationScheduling } from './notification'
import { Notification, NotificationRecipient, NotificationChannel, NotificationRead, DeliveryChannel, PriorityCount, ChannelStats } from './notification'

import type { NotificationStatus, ChannelType } from './enums'
import { NotificationPriority } from './enums'
import { TimeRange } from '../common';

// Notification Creation APIs
export interface CreateNotificationRequest extends CreateRequest<NotificationData> {
  data: NotificationData;
  recipients: NotificationRecipient[];
  channels: NotificationChannel[];
  priority: NotificationPriority;
  scheduling?: NotificationScheduling;
}

export interface CreateNotificationResponse extends CreateResponse<Notification> {
  data: Notification;
  notificationId: string;
  estimatedDelivery: string;
  deliveryChannels: DeliveryChannel[];
}

// Notification Retrieval APIs
export interface GetNotificationsRequest extends ListRequest {
  recipientId?: string;
  status?: NotificationStatus[];
  priority?: NotificationPriority[];
  channels?: string[];
  read?: boolean;
  timeRange?: NotificationTimeRange;
}

export interface GetNotificationsResponse extends ListResponse<Notification> {
  data: Notification[];
  unreadCount: number;
  priorityCounts: PriorityCount[];
  channelStats: ChannelStats[];
}

// Notification Management APIs
export interface MarkNotificationReadRequest extends BaseApiRequest {
  notificationId: string;
  readBy: string;
  readAt?: string;
  context: MultiTenantContext;
}

export interface MarkNotificationReadResponse extends BaseApiResponse<NotificationRead> {
  data: NotificationRead;
  readAt: string;
  remainingUnread: number;
}

// Extended time range for notifications
export interface NotificationTimeRange extends TimeRange {
  timezone?: string;
}