import { ApiError } from './api';

/** Map a parse-related ApiError code to user-friendly copy. */
export function friendlyParseError(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case 'UNPARSEABLE':
      case 'FETCH_FAILED':
        return "We couldn't read a recipe from that. Try pasting the recipe text directly.";
      case 'URL_NOT_ALLOWED':
        return "That link can't be imported.";
      case 'PARSER_UNAVAILABLE':
        return 'Import is temporarily unavailable, please try again.';
      case 'INVALID_INPUT':
        return 'Please paste some recipe text or a link.';
      default:
        return error.message;
    }
  }
  return 'Something went wrong. Please try again.';
}
