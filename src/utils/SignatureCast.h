#pragma once
#ifndef INC_PARSELMOUTH_SIGNATURE_CAST_H
#define INC_PARSELMOUTH_SIGNATURE_CAST_H

#include <utility>

namespace parselmouth {
namespace signature_cast_placeholder {

struct _;

} // namespace signature_cast_placeholder

namespace detail {

template <typename Functor>
struct RemoveClass;

template <typename R, typename C, typename... A>
struct RemoveClass<R C::*(A...)> { using Type = R (A...); };

template <typename R, typename C, typename... A>
struct RemoveClass<R C::*(A...) const> { using Type = R (A...); };

template<typename Functor>
using RemoveClassT = typename RemoveClass<Functor>::Type;


template<typename Signature, typename Function>
struct CompleteSignatureImpl;

template<typename Return, typename... Args, typename R, typename... A>
struct CompleteSignatureImpl<Return (Args...), R (A...)> {
	using _ = signature_cast_placeholder::_;
	using Type = std::conditional_t<std::is_same<Return, _>::value, R, Return> (std::conditional_t<std::is_same<Args, _>::value, A, Args>...);
};


template<typename Signature, typename Function>
struct CompleteSignature : CompleteSignatureImpl<Signature, RemoveClassT<decltype(&Function::operator())>> {};

template<typename Signature, typename R, typename... A>
struct CompleteSignature<Signature, R (&)(A...)> : CompleteSignatureImpl<Signature, R (A...)> {};

template<typename Signature, typename R, typename... A>
struct CompleteSignature<Signature, R (*)(A...)> : CompleteSignatureImpl<Signature, R (A...)> {};

template<typename Signature, typename R, typename C, typename... A>
struct CompleteSignature<Signature, R (C::*)(A...)> : CompleteSignatureImpl<Signature, R (C &, A...)> {};

template<typename Signature, typename R, typename C, typename... A>
struct CompleteSignature<Signature, R (C::*)(A...) const> : CompleteSignatureImpl<Signature, R (const C &, A...)> {};


template<typename Signature>
struct SignatureCastImpl;

template<typename Return, typename... Args>
struct SignatureCastImpl<Return (Args...)> {
	template<typename Function>
	static auto exec(Function &&f) { return [f = std::forward<Function>(f)](Args... args) -> Return { return f(std::forward<Args>(args)...); }; }

	template<typename R, typename... A>
	static auto exec(R (*f)(A...)) { return [f](Args... args) -> Return { return f(std::forward<Args>(args)...); }; }

	template<typename R, typename C, typename... A>
	static auto exec(R (C::*f)(A...)) { return [f](C &c, Args... args) -> Return { return c.*f(std::forward<Args>(args)...); }; }

	template<typename R, typename C, typename... A>
	static auto exec(R (C::*f)(A...) const) { return [f](const C &c, Args... args) -> Return { return c.*f(std::forward<Args>(args)...); };	}
};

} // namespace detail

template<typename Signature, typename Function>
auto signature_cast(Function &&f) {
	return detail::SignatureCastImpl<typename detail::CompleteSignature<Signature, Function>::Type>::exec(std::forward<Function>(f));
}

} // namespace parselmouth

#endif // INC_PARSELMOUTH_SIGNATURE_CAST_H
